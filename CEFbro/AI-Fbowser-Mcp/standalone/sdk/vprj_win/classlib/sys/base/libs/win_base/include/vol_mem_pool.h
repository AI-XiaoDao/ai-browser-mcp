
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_MEM_POOL_H__
#define __VOL_MEM_POOL_H__

// 为快速内存分配机制所预先分配的缓存池的相关参数,可以根据实际需要自行调节:

#ifndef _VOL_MEM_POOL_BLOCK_SIZE
    #define _VOL_MEM_POOL_BLOCK_SIZE  1  // 缓存池中每一个内存块的尺寸,单位为256字节.
#endif

// 缓存池中预先分配的内存块数目
#ifndef _VOL_NUM_MEM_POOL_BLOCKS
#ifdef _VOL_DLL  // 为编译DLL?
    #define _VOL_NUM_MEM_POOL_BLOCKS  (2 * 1024)
#else
    #define _VOL_NUM_MEM_POOL_BLOCKS  (16 * 1024)
#endif
#endif

#if _VOL_MEM_POOL_BLOCK_SIZE < 1
    #undef _VOL_MEM_POOL_BLOCK_SIZE
    #define _VOL_MEM_POOL_BLOCK_SIZE 1
#endif

#if _VOL_NUM_MEM_POOL_BLOCKS < 1024
    #undef _VOL_NUM_MEM_POOL_BLOCKS
    #define _VOL_NUM_MEM_POOL_BLOCKS 1024
#endif

//--------------------------------------------------------------------------------------

#ifdef _PF_WINDOWS  // 定义Windows下的SpinLock支持函数

extern "C" void _spin_lock (volatile INT_P* pSpinLocker);
extern "C" INT_P _spin_trylock (volatile INT_P* pSpinLocker);

#endif

// 自旋锁. 注意在同一线程中不能在已经锁住本锁的情况下再次尝试加锁.
class CVolSpinLock
{
public:
    inline_ CVolSpinLock ()
    {
    #ifdef _PF_WINDOWS
        m_lock = 1;
    #else
        VERIFY_EQUAL (pthread_spin_init (&m_lock, PTHREAD_PROCESS_PRIVATE), 0);
    #endif
    }

    inline_ ~CVolSpinLock ()
    {
    #ifndef _PF_WINDOWS
        VERIFY_EQUAL (pthread_spin_destroy (&m_lock), 0);
    #endif
    }

public:
    // 加锁. 注意如果在同一线程中多次加锁会死锁.
    // 如果blTry为真,则会尝试加锁,如果能够加锁,则锁住后返回真,如果不能则返回假.
    // 如果blTry为假,则会一直等待,直到能够成功加锁.
    inline_ BOOL lock (const BOOL blTry = FALSE) const
    {
    #ifdef _PF_WINDOWS
        if (blTry)
            return (_spin_trylock (&m_lock) == 0);
        _spin_lock (&m_lock);
        return TRUE;
    #else
        if (blTry)
            return (pthread_spin_trylock (&m_lock) == 0);
        else
            return (pthread_spin_lock (&m_lock) == 0);
    #endif
    }

    // 解除加锁
    inline_ void unlock () const
    {
    #ifdef _PF_WINDOWS
        m_lock = 1;
    #else
        VERIFY_EQUAL (pthread_spin_unlock (&m_lock), 0);
    #endif
    }

protected:
#ifdef _PF_WINDOWS
    mutable volatile INT_P m_lock;
#else
    mutable volatile pthread_spinlock_t m_lock;
#endif
};

//--------------------------------------------------------------------------------------

// 基于缓存池的内存快速分配类(支持多线程)
class CPoolMem
{
public:
    // npBlockSize: 单个缓存块的尺寸.对于小于等于该尺寸的内存,能够在内存池内直接快速分配.必须大于0.
    // npNumBlocks: 所预先准备用作分配的缓存块数目.必须大于0.
    CPoolMem (const INT_P npBlockSize, const INT_P npNumBlocks);

    virtual ~CPoolMem ();

public:
    // 分配指定尺寸内存(该尺寸可以为任意值),成功返回所分配内存指针,失败退出应用程序.
    void* Alloc (const INT_P npSize);

    // 分配指定尺寸内存(该尺寸可以为任意值),成功返回非NULL指针,失败返回NULL.
    void* AllocMaybeRetNull (const INT_P npSize);

    // 重分配指定尺寸内存,p必须为本对象的Alloc/Realloc方法返回值.
    // 成功返回所重分配内存指针,失败退出应用程序.
    void* Realloc (const void* p, const INT_P npNewSize);

    // 重分配指定尺寸内存(该尺寸可以为任意值),成功返回非NULL指针,失败返回NULL.
    void* ReallocMaybeRetNull (const void* p, const INT_P npNewSize);

    // 释放通过本对象所分配/重分配的内存
    void Free (const void* p);

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
    void DumpReport () const;
#endif

protected:
    BYTE* m_pbBufferBegin;    // 内存池的起始地址
    BYTE* m_pbBufferEnd;      // 内存池的结束地址
    BYTE* m_pbCurrentBlock;   // 指向内存池中当前尚未被分配缓存块的头部
    INT_P m_npPoolBlockSize;  // 内存池中单个缓存块的尺寸

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
    INT_P m_npNumBlocks;  // 内存池中预分配缓存块的总数
    INT_P m_npNumAllocedBlocks;  // 记录已经在内存池中分配出去的缓存块数目
    INT_P m_npNumMaxAllocedBlocks;  // 记录在内存池中同时分配出去的最大缓存块数目
    INT_P m_npNumTotalAllocTimes;  // 记录总共分配内存的次数
    INT_P m_npNumTotalAllocedInCacheTimes;  // 记录总共在内存池中分配内存的次数
#endif

    CVolSpinLock m_locker;  // 用作支持多线程操作的自旋锁对象
};

//-------------------------------------------------------------------------------

struct POOL_REGION_HEADER
{
    BYTE* m_pbCurrentBlock;  // 指向缓冲区内当前尚未被分配块的头部
    INT_P m_npNumAllocedBlocks;  // 本区域内已经被分配块的数目
    struct POOL_REGION_HEADER* m_pNextRegion; // 下一个内存区域
};
typedef struct POOL_REGION_HEADER POOL_REGION_HEADER;
// 区域头后为m_npNumBlocksInRegion个尺寸为m_npBlockSize的内存块集合.

//   已分配内存区域缩减模式
//   正常情况下,如果一个区域内的内存块已经被全部释放,则该区域将被释放.根据应用场合指定恰当的此
// 模式可以减少内存分配释放的频率,又不至于导致太多的内存浪费.
typedef enum
{
    RSM_KEEP_NONE, //   不保留区域. 所有其中内存块已经被全部释放的区域将被立即释放,适用于对于内存浪费比较敏感的场合.
    RSM_KEEP_ONE,  //   保留一个区域用作以后快速分配内存块,其它区域将被正常释放.
    RSM_KEEP_ALL,  //   保留所有区域(只要区域被分配,就将其保留,哪怕其中的内存块已经被全部释放).
                    // 适用于对于内存浪费不敏感但是需要最快的内存块分配速度的场合(譬如服务器软件).
}
REGION_SHRINK_MODE;

// 支持池缓冲的内存块分配类(注意本类不是多线程安全的)
class CBlockPoolMem
{
public:
    //   npBlockSize指定每次分配的内存块尺寸
    //   每次当需要扩展内存池时就会分配一个新的内存区域,npNumBlocksInRegion指定该区域中的内存块数目.
    // 也就是说内存池每次扩展尺寸为npBlockSize*npNumBlocksInRegion.此参数值越大本类的执行效率就越高,
    // 当然所可能浪费的空闲内存空间就越多.
    CBlockPoolMem (const INT_P npBlockSize, const INT_P npNumBlocksInRegion = 64,
            const REGION_SHRINK_MODE enShrinkMode = RSM_KEEP_ONE);
    virtual ~CBlockPoolMem ();

public:
    // 重新设置配置参数,所有已经分配出去的内存块都将被自动释放.
    // npBlockSize或npNumBlocksInRegion为-1表示维持原值不变.
    void Reset (const INT_P npBlockSize, const INT_P npNumBlocksInRegion = -1);

    virtual void* AllocBlock ();  // 分配一段尺寸为m_npBlockSize的内存块
    virtual void FreeBlock (const void* pBlock);  // 分配出去的内存块可以调用本方法释放,本方法支持所设置的内存区域缩减模式.
    virtual void FreeAll ();  // 释放全部缓冲池内存块. 注意本方法忽略所设置的内存区域缩减模式,始终释放全部内存区域.
    BOOL_P IsValid (const void* p);  // 返回指定地址指针是否处于本对象已经分配的有效内存中

    inline_ INT_P GetBlockSize () const
    {
        return m_npBlockSize;
    }

    // 计算返回当前已经分配块的数目
    INT_P CalcNumAllocedBlocks () const;

protected:
    void _init (const INT_P npBlockSize, const INT_P npNumBlocksInRegion);

private:
    POOL_REGION_HEADER* m_pFirstRegion;  // 首区域

    REGION_SHRINK_MODE m_enShrinkMode;  // 已分配内存区域缩减模式
    INT_P m_npNumBlocksInRegion;  // 每个区域中的块数目
    INT_P m_npBlockSize;  // 每个内存块的尺寸
    INT_P m_npRegionSize;  // 每个区域数据部分的尺寸,等于 m_npNumBlocksInRegion * m_npBlockSize
};

#endif
