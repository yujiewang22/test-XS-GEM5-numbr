/*
 * Copyright (c) 2012-2014,2017-2018,2020-2021 ARM Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder.  You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2004-2006 The Regents of The University of Michigan
 * Copyright (c) 2013 Advanced Micro Devices, Inc.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __CPU_O3_LSQ_UNIT_HH__
#define __CPU_O3_LSQ_UNIT_HH__

#include <algorithm>
#include <bitset>
#include <cstdint>
#include <cstring>
#include <map>
#include <memory>
#include <queue>
#include <vector>

#include <base/logging.hh>
#include <boost/circular_buffer.hpp>

#include "arch/generic/debugfaults.hh"
#include "arch/generic/vec_reg.hh"
#include "base/circular_queue.hh"
#include "config/the_isa.hh"
#include "cpu/base.hh"
#include "cpu/inst_seq.hh"
#include "cpu/o3/comm.hh"
#include "cpu/o3/cpu.hh"
#include "cpu/o3/dyn_inst_ptr.hh"
#include "cpu/o3/limits.hh"
#include "cpu/o3/lsq.hh"
#include "cpu/timebuf.hh"
#include "debug/HtmCpu.hh"
#include "debug/LSQUnit.hh"
#include "mem/packet.hh"
#include "mem/port.hh"

namespace gem5
{

struct BaseO3CPUParams;

namespace o3
{

enum class SplitStoreStatus
{
    AddressReady,
    DataReady,
    StaPipeFinish,
    StdPipeFinish
};

class IEW;

class StoreBufferEntry
{
  public:
    const int index;
    Addr blockVaddr;
    Addr blockPaddr;
    std::vector<uint8_t> blockDatas;
    std::vector<bool> validMask;
    bool sending;
    // the another same addr entry when sending
    // another cannot sending until self sending finished
    StoreBufferEntry* vice = nullptr;
    // merged request
    LSQ::SbufferRequest* request = nullptr;

    StoreBufferEntry(int size, int index) : index(index) {
        blockDatas.resize(size, 0);
        validMask.resize(size, false);
    }

    void reset(uint64_t blockVaddr, uint64_t blockPaddr, uint64_t offset, uint8_t* datas, uint64_t size);

    void merge(uint64_t offset, uint8_t* datas, uint64_t size);

    bool recordForward(RequestPtr req, LSQ::LSQRequest* lsqreq);
};

class StoreBuffer
{
    using mapIter = typename std::unordered_map<int, StoreBufferEntry*>::iterator;

    // key = (paddr & cacheblockmask)
    uint64_t _size;
    std::unordered_map<int, StoreBufferEntry*> data_map;
    std::vector<mapIter> crossRef;
    boost::circular_buffer<int> lru_index;
    boost::circular_buffer<int> free_list;
    std::vector<StoreBufferEntry*> data_vec;
    std::vector<bool> data_vld;

public:

    void setData(std::vector<StoreBufferEntry*>& data_vec);
    bool full();
    uint64_t size();
    uint64_t unsentSize();
    StoreBufferEntry* getEmpty();
    void insert(int index, uint64_t addr);
    StoreBufferEntry* get(uint64_t addr);
    void update(int index);
    StoreBufferEntry* getEvict();
    StoreBufferEntry* createVice(StoreBufferEntry* entry);
    void release(StoreBufferEntry* entry);
};

/**
 * Class that implements the actual LQ and SQ for each specific
 * thread.  Both are circular queues; load entries are freed upon
 * committing, while store entries are freed once they writeback. The
 * LSQUnit tracks if there are memory ordering violations, and also
 * detects partial load to store forwarding cases (a store only has
 * part of a load's data) that requires the load to wait until the
 * store writes back. In the former case it holds onto the instruction
 * until the dependence unit looks at it, and in the latter it stalls
 * the LSQ until the store writes back. At that point the load is
 * replayed.
 */
class LSQUnit
{
  public:
    static constexpr auto MaxDataBytes = MaxVecRegLenInBytes;

    using LSQRequest = LSQ::LSQRequest;
  private:
    class LSQEntry
    {
      private:
        /** The instruction. */
        DynInstPtr _inst;
        /** The request. */
        LSQRequest* _request = nullptr;
        /** The size of the operation. */
        uint32_t _size = 0;
        /** Valid entry. */
        bool _valid = false;

      public:
        ~LSQEntry()
        {
            if (_request != nullptr) {
                _request->freeLSQEntry();
                _request = nullptr;
            }
        }

        void
        clear()
        {
            _inst = nullptr;
            if (_request != nullptr) {
                _request->freeLSQEntry();
            }
            _request = nullptr;
            _valid = false;
            _size = 0;
        }

        void
        set(const DynInstPtr& new_inst)
        {
            assert(!_valid);
            _inst = new_inst;
            _valid = true;
            _size = 0;
        }

        LSQRequest* request() { return _request; }
        void setRequest(LSQRequest* r) { _request = r; }
        bool hasRequest() { return _request != nullptr; }
        /** Member accessors. */
        /** @{ */
        bool valid() const { return _valid; }
        uint32_t& size() { return _size; }
        const uint32_t& size() const { return _size; }
        const DynInstPtr& instruction() const { return _inst; }
        /** @} */
    };

    class SQEntry : public LSQEntry
    {
      private:
        /** The store data. */
        char _data[MaxDataBytes];
        /** Whether or not the store can writeback. */
        bool _canWB = false;
        /** Whether or not the store is committed. */
        bool _committed = false;
        /** Whether or not the store is completed. */
        bool _completed = false;
        /** Does this request write all zeros and thus doesn't
         * have any data attached to it. Used for cache block zero
         * style instructs (ARM DC ZVA; ALPHA WH64)
         */
        bool _isAllZeros = false;

        bool _addrReady = false;

        bool _dataReady = false;

        bool _staFinish = false;

        bool _stdFinish = false;

      public:
        static constexpr size_t DataSize = sizeof(_data);
        /** Constructs an empty store queue entry. */
        SQEntry()
        {
            std::memset(_data, 0, DataSize);
        }

        void set(const DynInstPtr& inst) { LSQEntry::set(inst); }

        void
        clear()
        {
            LSQEntry::clear();
            _canWB = _completed = _committed = _isAllZeros = false;
            _addrReady = _dataReady = _staFinish = _stdFinish = false;
        }

        void setStatus(SplitStoreStatus status);

        bool addrReady() const { return _addrReady; }
        bool dataReady() const { return _dataReady; }
        bool canForwardToLoad() const { return _addrReady && _dataReady; }
        bool splitStoreFinish() const { return _staFinish && _stdFinish; }

        /** Member accessors. */
        /** @{ */
        bool& canWB() { return _canWB; }
        const bool& canWB() const { return _canWB; }
        bool& completed() { return _completed; }
        const bool& completed() const { return _completed; }
        bool& committed() { return _committed; }
        const bool& committed() const { return _committed; }
        bool& isAllZeros() { return _isAllZeros; }
        const bool& isAllZeros() const { return _isAllZeros; }
        char* data() { return _data; }
        const char* data() const { return _data; }
        /** @} */
    };
    using LQEntry = LSQEntry;

  public:
    // storeQue -> storeBuffer -> cache
    const int maxSQoffload = 2;
    const int sqFullBufferSize = 4;

    int sqFullUpperLimit = 0;
    int sqFullLowerLimit = 0;
    bool storeBufferFlushing = false;
    bool sqWillFull = false;
    const uint32_t sbufferEvictThreshold = 0;
    const uint32_t sbufferEntries = 0;
    StoreBuffer storeBuffer;
    // Store Buffer Writeback Timeout
    uint64_t storeBufferWritebackInactive;
    uint64_t storeBufferInactiveThreshold;

    StoreBufferEntry* blockedsbufferEntry = nullptr;

    /** Coverage of one address range with another */
    enum class AddrRangeCoverage
    {
        PartialAddrRangeCoverage, /* Two ranges partly overlap */
        FullAddrRangeCoverage, /* One range fully covers another */
        NoAddrRangeCoverage /* Two ranges are disjoint */
    };

  public:
    using LoadQueue = CircularQueue<LQEntry>;
    using StoreQueue = CircularQueue<SQEntry>;

    std::vector<LSQRequest*> inflightLoads;

  public:
    /** Constructs an LSQ unit. init() must be called prior to use. */
    LSQUnit(uint32_t lqEntries, uint32_t sqEntries, uint32_t sbufferEntries,
      uint32_t sbufferEvictThreshold, uint64_t storeBufferInactiveThreshold,
      uint32_t ldPipeStages, uint32_t stPipeStages);

    /** We cannot copy LSQUnit because it has stats for which copy
     * contructor is deleted explicitly. However, STL vector requires
     * a valid copy constructor for the base type at compile time.
     */
    LSQUnit(const LSQUnit &l) : stats(nullptr)
    {
        panic("LSQUnit is not copy-able");
    }

    /** Initializes the LSQ unit with the specified number of entries. */
    void init(CPU *cpu_ptr, IEW *iew_ptr, const BaseO3CPUParams &params,
            LSQ *lsq_ptr, unsigned id);

    /** Returns the name of the LSQ unit. */
    std::string name() const;

    /** Sets the pointer to the dcache port. */
    void setDcachePort(RequestPort *dcache_port);

    /** Perform sanity checks after a drain. */
    void drainSanityCheck() const;

    /** Takes over from another CPU's thread. */
    void takeOverFrom();

    /** Inserts an instruction. */
    void insert(const DynInstPtr &inst);
    /** Inserts a load instruction. */
    void insertLoad(const DynInstPtr &load_inst);
    /** Inserts a store instruction. */
    void insertStore(const DynInstPtr &store_inst);

    /** Check for ordering violations in the LSQ. For a store squash if we
     * ever find a conflicting load. For a load, only squash if we
     * an external snoop invalidate has been seen for that load address
     * @param load_idx index to start checking at
     * @param inst the instruction to check
     */
    Fault checkViolations(typename LoadQueue::iterator& loadIt,
            const DynInstPtr& inst);

    /** A load replay helper function
     * this function will clear state of inst (the original request, tlb state etc)
     * insert to CacheMissReplayQ or replayQ and set as Replayed in pipeline
     * @param cacheMiss insert to CacheMissReplayQ
     * @param fastReplay insert to replayQ
     * @param dropReqNow call request->discard() now
     */
    void loadReplayHelper(DynInstPtr inst, LSQRequest* request, bool cacheMiss,
            bool fastReplay, bool dropReqNow);

    /** Check if an incoming invalidate hits in the lsq on a load
     * that might have issued out of order wrt another load beacuse
     * of the intermediate invalidate.
     */
    void checkSnoop(PacketPtr pkt);

    /** Iq issues a load to load pipeline. */
    void issueToLoadPipe(const DynInstPtr &inst);

    bool triggerStorePFTrain(int sq_idx);

    /** Executes an amo instruction. */
    Fault executeAmo(const DynInstPtr& inst);

    /** Iq issues a store to store pipeline. */
    void issueToStorePipe(const DynInstPtr &inst);

    /** Commits the head load. */
    void commitLoad();
    /** Commits loads older than a specific sequence number. */
    void commitLoads(InstSeqNum &youngest_inst);

    /** Commits stores older than a specific sequence number. */
    void commitStores(InstSeqNum &youngest_inst);

    bool directStoreToCache();

    /** Writes back stores. */
    void offloadToStoreBuffer();

    bool insertStoreBuffer(Addr vaddr, Addr paddr, uint8_t* datas, uint64_t size);

    void storeBufferEvictToCache();

    void flushStoreBuffer();

    bool storeBufferEmpty() { return storeBuffer.size() == 0; }

    void completeSbufferEvict(PacketPtr pkt);

    /** Completes the data access that has been returned from the
     * memory system. */
    void completeDataAccess(PacketPtr pkt);

    /** Squashes all instructions younger than a specific sequence number. */
    void squash(const InstSeqNum &squashed_num);

    /** Returns if there is a memory ordering violation. Value is reset upon
     * call to getMemDepViolator().
     */
    bool violation() { return memDepViolator; }

    /** Returns the memory ordering violator. */
    DynInstPtr getMemDepViolator();

    /** Check if store should skip this raw violation because of nuke replay. */
    bool skipNukeReplay(const DynInstPtr& load_inst);

    /** Check if there exists raw nuke between load and store. */
    bool pipeLineNukeCheck(const DynInstPtr &load_inst, const DynInstPtr &store_inst);

    /** Returns the number of free LQ entries. */
    unsigned numFreeLoadEntries();

    /** Returns the number of free SQ entries. */
    unsigned numFreeStoreEntries();

    /** Returns the number of Poped LQ entries in LAST CLOCK. */
    unsigned getAndResetLastClockLQPopEntries();

    /** Returns the number of Poped SQ entries in LAST CLOCK. */
    unsigned getAndResetLastClockSQPopEntries();

    /** Returns the number of loads in the LQ. */
    int numLoads() { return loadQueue.size(); }

    /** Returns the number of stores in the SQ. */
    int numStores() { return storeQueue.size(); }

    // hardware transactional memory
    int numHtmStarts() const { return htmStarts; }
    int numHtmStops() const { return htmStops; }
    void resetHtmStartsStops() { htmStarts = htmStops = 0; }
    uint64_t getLatestHtmUid() const;
    void
    setLastRetiredHtmUid(uint64_t htm_uid)
    {
        assert(htm_uid >= lastRetiredHtmUid);
        lastRetiredHtmUid = htm_uid;
    }

    // Stale translation checks
    void startStaleTranslationFlush();
    bool checkStaleTranslations() const;

    /** Returns if either the LQ or SQ is full. */
    bool isFull() { return lqFull() || sqFull(); }

    /** Returns if both the LQ and SQ are empty. */
    bool isEmpty() const { return lqEmpty() && sqEmpty(); }

    /** Returns if the LQ is full. */
    bool lqFull() { return loadQueue.full(); }

    /** Returns if the SQ is full. */
    bool sqFull() { return storeQueue.full(); }

    /** Returns if the LQ is empty. */
    bool lqEmpty() const { return loadQueue.size() == 0; }

    /** Returns if the SQ is empty. */
    bool sqEmpty() const { return storeQueue.size() == 0; }

    /** Returns the number of instructions in the LSQ. */
    unsigned getCount() { return loadQueue.size() + storeQueue.size(); }

    /** Returns if there are any stores to writeback. */
    bool hasStoresToWB() { return storesToWB > 0; }

    /** Returns the number of stores to writeback. */
    int numStoresToSbuffer() { return storesToWB; }

    /** get description string from load/store pipeLine flag. */
    std::string getLdStFlagStr(const std::bitset<LdStFlagNum>& flag)
    {
        std::string res{};
        for (int i = 0; i < LdStFlagNum; i++) {
            if (flag.test(i)) {
                res += LdStFlagName[i] + ": [1] ";
            } else {
                res += LdStFlagName[i] + ": [0] ";
            }
        }
        return res;
    }

    LSQ* getLsq() { return lsq; }

    /** Returns if the LSQ unit will writeback on this cycle. */
    bool
    willWB()
    {
        bool t = storeWBIt.dereferenceable() &&
                        storeWBIt->valid() &&
                        storeWBIt->canWB() &&
                        !storeWBIt->completed() &&
                        !isStoreBlocked;
        return t || storeBufferFlushing;
    }

    /** Handles doing the retry. */
    void recvRetry();

    unsigned int cacheLineSize();

    PacketPtr makeFullFwdPkt(DynInstPtr load_inst, LSQRequest *request);
  private:
    /** Reset the LSQ state */
    void resetState();

    /** Writes back the instruction, sending it to IEW. */
    void writeback(const DynInstPtr &inst, PacketPtr pkt);

    /** Try to finish a previously blocked write back attempt */
    void writebackBlockedStore();

    /** Completes the store at the specified index. */
    void completeStore(typename StoreQueue::iterator store_idx, bool from_sbuffer = false);

    /** Handles completing the send of a store to memory. */
    void storePostSend();

  public:
    /** Attempts to send a packet to the cache.
     * Check if there are ports available. Return true if
     * there are, false if there are not.
     */
    void bankConflictReplaySchedule();

    void tagReadFailReplaySchedule();

    bool trySendPacket(bool isLoad, PacketPtr data_pkt, bool &bank_conflict, bool &tag_read_fail);

    bool sbufferSendPacket(PacketPtr data_pkt);

    /** Debugging function to dump instructions in the LoadPipe. */
    void dumpLoadPipe();

    /** Debugging function to dump instructions in the storePipe. */
    void dumpStorePipe();

    /** Debugging function to dump instructions in the LSQ. */
    void dumpInsts() const;

    /** Ticks
     *  causing load/store pipe to run for one cycle.
     */
    void tick();

    /** Process instructions in each load pipeline stages. */
    void executeLoadPipeSx();

    /**
     * - stage0: normal inst access TLB, atomic access TLB and try send to cache.
     * - stage1: normal inst try send to cache.
     * - stage2: Analyze the flag and try to send the inst to commit.
     * - stage3: now just return fault and do nothing.
     */
    Fault loadPipeS0(const DynInstPtr &inst, std::bitset<LdStFlagNum> &flag);
    Fault loadPipeS1(const DynInstPtr &inst, std::bitset<LdStFlagNum> &flag);
    Fault loadPipeS2(const DynInstPtr &inst, std::bitset<LdStFlagNum> &flag);
    Fault loadPipeS3(const DynInstPtr &inst, std::bitset<LdStFlagNum> &flag);

    /** Process instructions in each store pipeline stages. */
    void executeStorePipeSx();

    /**
     * - stage0: access TLB
     * - stage1: save data to store queue, check load violations, set memDepViolator
     */
    Fault storePipeS0(const DynInstPtr &inst, std::bitset<LdStFlagNum> &flag);
    Fault storePipeS1(const DynInstPtr &inst, std::bitset<LdStFlagNum> &flag);
    Fault emptyStorePipeSx(const DynInstPtr &inst, std::bitset<LdStFlagNum> &flag, uint64_t stage);

    /** Wrap function. */
    void executePipeSx();

    /** Schedule event for the cpu. */
    void schedule(Event& ev, Tick when);

    BaseMMU *getMMUPtr();

  private:
    System *system;

    /** Pointer to the CPU. */
    CPU *cpu;

    /** Pointer to the IEW stage. */
    IEW *iewStage;

    /** Pointer to the LSQ. */
    LSQ *lsq;

    /** Pointer to the dcache port.  Used only for sending. */
    RequestPort *dcachePort;

    /** Writeback event, specifically for when stores forward data to loads. */
    class WritebackEvent : public Event
    {
      public:
        /** Constructs a writeback event. */
        WritebackEvent(const DynInstPtr &_inst, PacketPtr pkt,
                LSQUnit *lsq_ptr);

        /** Processes the writeback event. */
        void process();

        /** Returns the description of this event. */
        const char *description() const;

      private:
        /** Instruction whose results are being written back. */
        DynInstPtr inst;

        /** The packet that would have been sent to memory. */
        PacketPtr pkt;

        /** The pointer to the LSQ unit that issued the store. */
        LSQUnit *lsqPtr;
    };
    class bankConflictReplayEvent : public Event
    {
      public:
        /** Constructs a bankConflict event. */
        bankConflictReplayEvent(LSQUnit *lsq_ptr);

        /** Processes the bankConflict event. */
        void process();

        /** Returns the description of this event. */
        const char *description() const;

      private:
        /** The pointer to the LSQ unit that issued the bankConflictReplayEvent. */
        LSQUnit *lsqPtr;
    };
    class tagReadFailReplayEvent : public Event
    {
      public:
        /** Constructs a tagReadFail event. */
        tagReadFailReplayEvent(LSQUnit *lsq_ptr);

        /** Processes the tagReadFail event. */
        void process();

        /** Returns the description of this event. */
        const char *description() const;

      private:
        /** The pointer to the LSQ unit that issued the tagReadFailReplayEvent. */
        LSQUnit *lsqPtr;
    };

    bool enableStorePrefetchTrain;

  public:
    /**
     * Handles writing back and completing the load or store that has
     * returned from memory.
     *
     * @param pkt Response packet from the memory sub-system
     */
    bool recvTimingResp(PacketPtr pkt);

    /** The LSQUnit thread id. */
    ThreadID lsqID;
  public:
    /** The store queue. */
    StoreQueue storeQueue;
    /** The load queue. */
    LoadQueue loadQueue;

    /** Struct that defines the information passed through Load Pipeline. */
    struct LoadPipeStruct
    {
        int size;

        DynInstPtr insts[MaxWidth];
        std::bitset<LdStFlagNum> flags[MaxWidth];
    };
    /** The load pipeline TimeBuffer. */
    TimeBuffer<LoadPipeStruct> loadPipe;
    /** Each stage in load pipeline. loadPipeSx[0] means load pipe S0 */
    std::vector<TimeBuffer<LoadPipeStruct>::wire> loadPipeSx;

    /** Struct that defines the information passed through Store Pipeline. */
    struct StorePipeStruct
    {
        int size;

        DynInstPtr insts[MaxWidth];
        std::bitset<LdStFlagNum> flags[MaxWidth];
    };
    /** The store pipeline TimeBuffer. */
    TimeBuffer<StorePipeStruct> storePipe;
    /** Each stage in store pipeline. storePipeSx[0] means store pipe S0 */
    std::vector<TimeBuffer<StorePipeStruct>::wire> storePipeSx;

    /** Find inst in Load/Store Pipeline, set corresponding flag to true */
    void setFlagInPipeLine(DynInstPtr inst, LdStFlags f);

  private:
    /** The number of places to shift addresses in the LSQ before checking
     * for dependency violations
     */
    unsigned depCheckShift;

    /** Should loads be checked for dependency issues */
    bool checkLoads;

    /** The number of store instructions in the SQ waiting to writeback. */
    int storesToWB;

    // hardware transactional memory
    // nesting depth
    int htmStarts;
    int htmStops;
    // sanity checks and debugging
    uint64_t lastRetiredHtmUid;

    /** The index of the first instruction that may be ready to be
     * written back, and has not yet been written back.
     */
    typename StoreQueue::iterator storeWBIt;

    /** Address Mask for a cache block (e.g. ~(cache_block_size-1)) */
    Addr cacheBlockMask;

    /** Wire to read information from the issue stage time queue. */
    typename TimeBuffer<IssueStruct>::wire fromIssue;

    /** Whether or not the LSQ is stalled. */
    bool stalled;
    /** The store that causes the stall due to partial store to load
     * forwarding.
     */
    InstSeqNum stallingStoreIsn;
    /** The index of the above store. */
    ssize_t stallingLoadIdx;

    /** The packet that needs to be retried. */
    PacketPtr retryPkt;

    /** Whehter or not a store is blocked due to the memory system. */
    bool isStoreBlocked;

    bool storeBlockedfromQue;

    bool sbufferStall;

    /** Whether or not a store is in flight. */
    bool storeInFlight;

    /** The oldest load that caused a memory ordering violation. */
    DynInstPtr memDepViolator;

    /** Flag for memory model. */
    bool needsTSO;

    unsigned lastClockSQPopEntries;
    unsigned lastClockLQPopEntries;

  protected:
    // Will also need how many read/write ports the Dcache has.  Or keep track
    // of that in stage that is one level up, and only call executeLoad/Store
    // the appropriate number of times.
    struct LSQUnitStats : public statistics::Group
    {
        LSQUnitStats(statistics::Group *parent);

        /** Total number of loads forwaded from LSQ stores. */
        statistics::Scalar forwLoads;

        /** Total number of squashed loads. */
        statistics::Scalar squashedLoads;

        /** Total number of pipeline detected raw nuke. */
        statistics::Scalar pipeRawNukeReplay;

        /** Total number of responses from the memory system that are
         * ignored due to the instruction already being squashed. */
        statistics::Scalar ignoredResponses;

        /** Tota number of memory ordering violations. */
        statistics::Scalar memOrderViolation;

        /** Tota number of successfully forwarding from bus. */
        statistics::Scalar busForwardSuccess;

        /** Tota number of early cache miss replay. */
        statistics::Scalar cacheMissReplayEarly;

        /** Total number of squashed stores. */
        statistics::Scalar squashedStores;

        /** Number of loads that were rescheduled. */
        statistics::Scalar rescheduledLoads;

        /**Number of bank conflict times**/
        statistics::Scalar bankConflictTimes;

        /** Number of bus append times **/
        statistics::Scalar busAppendTimes;

        /** Number of times the LSQ is blocked due to the cache. */
        statistics::Scalar blockedByCache;

        statistics::Scalar sbufferFull;

        statistics::Scalar sbufferCreateVice;

        statistics::Scalar sbufferEvictDuetoFlush;
        statistics::Scalar sbufferEvictDuetoFull;
        statistics::Scalar sbufferEvictDuetoSQFull;
        statistics::Scalar sbufferEvictDuetoTimeout;
        statistics::Scalar sbufferFullForward;
        statistics::Scalar sbufferPartiForward;

        /** Distribution of cycle latency between the first time a load
         * is issued and its completion */
        statistics::Distribution loadToUse;
        statistics::Distribution loadTranslationLat;


        statistics::Scalar forwardSTDNotReady;
        statistics::Scalar STAReadyFirst;
        statistics::Scalar STDReadyFirst;

        statistics::Scalar nonUnitStrideCross16Byte;
        statistics::Scalar unitStrideCross16Byte;
        statistics::Scalar unitStrideAligned;
    } stats;

    void bankConflictReplay();

    void tagReadFailReplay();

    bool squashMark{false};

  public:
    /** Load Forwards data from Data bus. */
    void forwardFrmBus(DynInstPtr inst, LSQRequest *request);

    /** Executes the load at the given index. */
    Fault read(LSQRequest *request, ssize_t load_idx);

    /** Executes the store at the given index. */
    Fault write(LSQRequest *requst, uint8_t *data, ssize_t store_idx);

    /** Returns the index of the head load instruction. */
    int getLoadHead() { return loadQueue.head(); }

    /** Returns the sequence number of the head load instruction. */
    InstSeqNum getLoadHeadSeqNum();

    /** Returns the index of the head store instruction. */
    int getStoreHead() { return storeQueue.head(); }
    /** Returns the sequence number of the head store instruction. */
    InstSeqNum getStoreHeadSeqNum();

    /** Returns whether or not the LSQ unit is stalled. */
    bool isStalled()  { return stalled; }

    LSQUnitStats* getStats() { return &stats; }
  public:
    typedef typename CircularQueue<LQEntry>::iterator LQIterator;
    typedef typename CircularQueue<SQEntry>::iterator SQIterator;
};

} // namespace o3
} // namespace gem5

#endif // __CPU_O3_LSQ_UNIT_HH__
