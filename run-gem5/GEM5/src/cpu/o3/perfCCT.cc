#include "cpu/o3/perfCCT.hh"

#include "cpu/o3/dyn_inst.hh"

namespace gem5
{
namespace o3
{

void
InstMeta::reset(const DynInstPtr inst)
{
    this->sn = inst->seqNum;
    posTick.clear();
    posTick.resize((int)PerfRecord::AtCommit + 1, 0);
    disasm = inst->staticInst->disassemble(inst->pcState().instAddr());
    pc = inst->pcState().instAddr();
}


PerfCCT::PerfCCT(bool enable, ArchDBer* db) : enableCCT(enable), archdb(db)
{
    if (enableCCT) {
        metas.resize(MaxMetas);

        ss << "INSERT INTO LifeTimeCommitTrace(";
        ss << PerfRecordStrings[0];
        for (int i=1; i < (int)PerfRecord::Num_PerfRecord; i++) {
            ss << "," << PerfRecordStrings[i];
        }
        ss << ") VALUES(";
        sql_insert_cmd = ss.str();
        ss.str(std::string());
    }
}

InstMeta*
PerfCCT::getMeta(InstSeqNum sn)
{
    auto& meta = metas[sn % MaxMetas];
    return &meta;
}

void
PerfCCT::createMeta(const DynInstPtr inst)
{
    if (!enableCCT) [[likely]] {
        return;
    }
    auto& old = metas[inst->seqNum % MaxMetas];
    old.reset(inst);
}

void
PerfCCT::updateInstPos(InstSeqNum sn, const PerfRecord pos)
{
    if (!enableCCT) [[likely]] {
        return;
    }
    auto meta = getMeta(sn);
    if (meta->posTick.at((int)pos)) return;
    meta->posTick.at((int)pos) = curTick();
}

void
PerfCCT::commitMeta(InstSeqNum sn)
{
    if (!enableCCT) [[likely]] {
        return;
    }
    auto meta = getMeta(sn);
    ss << sql_insert_cmd;
    // dump counter first
    ss << meta->posTick[0];
    for (auto it = meta->posTick.begin() + 1; it != meta->posTick.end(); it++) {
        ss << "," << *it;
    }
    // dump string last
    ss << ",\'" << meta->disasm << "\'";
    // pc is unsigned, but sqlite3 only supports signed integer [-2^63, 2^63-1]
    // if real pc > 2^63-1, it will be stored as negative number
    // (negtive pc = real pc - 2^64)
    // when read a negtive pc, real pc = negtive pc + 2^64
    ss << "," << int64_t(meta->pc);
    ss << ");";
    archdb->execmd(ss.str());
    ss.str(std::string());
}

}
}
