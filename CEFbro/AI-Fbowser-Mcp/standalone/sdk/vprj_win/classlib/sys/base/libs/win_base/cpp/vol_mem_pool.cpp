
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

//-------------------------------------------------------------------------------

#if defined (_PF_WIN32)

extern "C" void _spin_lock (volatile INT_P* pSpinLocker)
{
    _asm mov eax, pSpinLocker

L1:
    _asm lock dec dword ptr [eax]
    _asm jne L2
    
    return;

L2:
    _asm pause
    _asm cmp dword ptr [eax], 0
    _asm jg L1
    _asm jmp L2
}

extern "C" INT_P _spin_trylock (volatile INT_P* pSpinLocker)
{
    _asm mov edx, pSpinLocker
    _asm mov eax, 1
    _asm xor ecx, ecx
    _asm lock cmpxchg dword ptr [edx], ecx
    _asm jne L0

    return 0;
L0:
    return 16;  // EBUSY
}

#elif defined (_PF_WIN64)
    // Win64位下不支持嵌入汇编,必须采用外部库的方式引入.
    // #pragma comment (lib, "cpp\\asm_64\\spin_lock_64.lib")
#endif

//-------------------------------------------------------------  实际的内存管理函数

// 用作在调试版本下捕获内存垃圾
#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?

static INT_P s_npNumAllocedMemories = 0;  // 用作记录尚未释放的内存数目

#endif

#ifdef _PF_WINDOWS
    #define _USE_WINDOWS_PROCESS_HEAP
#endif

static void* sAllocMemory (const INT_P npSize)
{
    ASSERT (npSize > 0);

#ifdef _USE_WINDOWS_PROCESS_HEAP
    void* p = HeapAlloc (::GetProcessHeap (), 0, (UINT_P)npSize);
#else
    void* p = malloc (npSize);
#endif
    if (p == NULL)
    {
        FAIL;
        exit (-1);
    }

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
    INC_INTP_VAR_A (s_npNumAllocedMemories)
#endif
    return p;
}

static void* sAllocMemoryMaybeRetNull (const INT_P npSize)
{
    ASSERT (npSize > 0);

#ifdef _USE_WINDOWS_PROCESS_HEAP
    void* p = HeapAlloc (::GetProcessHeap (), 0, (UINT_P)npSize);
#else
    void* p = malloc (npSize);
#endif

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
    if (p != NULL)
    {
        INC_INTP_VAR_A (s_npNumAllocedMemories)
    }
#endif
    return p;
}

static void* sReallocMemory (const void* p, const INT_P npNewSize)
{
    ASSERT (p != NULL && npNewSize > 0);

#ifdef _USE_WINDOWS_PROCESS_HEAP
    p = HeapReAlloc (::GetProcessHeap (), 0, (void*)p, (UINT_P)npNewSize);
#else
    p = realloc ((void*)p, npNewSize);
#endif

    if (p == NULL)
    {
        FAIL;
        exit (-1);
    }
    return (void*)p;
}

static void* sReallocMemoryMaybeRetNull (const void* p, const INT_P npNewSize)
{
    ASSERT (p != NULL && npNewSize > 0);

#ifdef _USE_WINDOWS_PROCESS_HEAP
    return HeapReAlloc (::GetProcessHeap (), 0, (void*)p, (UINT_P)npNewSize);
#else
    return realloc ((void*)p, npNewSize);
#endif
}

static void sFreeMemory (const void* p)
{
    ASSERT (p != NULL);

#ifdef _USE_WINDOWS_PROCESS_HEAP
    VERIFY (HeapFree (::GetProcessHeap (), 0, (void*)p));
#else
    free ((void*)p);
#endif

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
    DEC_INTP_VAR_A (s_npNumAllocedMemories)
#endif
}

//-------------------------------------------------------------------------------

CPoolMem::CPoolMem (const INT_P npBlockSize, const INT_P npNumBlocks)
{
    ASSERT (npBlockSize > 0 && npNumBlocks > 0);

    m_npPoolBlockSize = MAX ((INT_P)sizeof (void*), npBlockSize);  // 块尺寸必须至少能保存一个指针
    // 将m_npPoolBlockSize对齐到sizeof (INT_P)
    INT_P np = m_npPoolBlockSize % (INT_P)sizeof (INT_P);
    if (np != 0)
        m_npPoolBlockSize += ((INT_P)sizeof (INT_P) - np);
    ASSERT (m_npPoolBlockSize > 0);

    // 分配内存池
    const INT_P npBufferSize = m_npPoolBlockSize * npNumBlocks;
    m_pbBufferBegin = m_pbCurrentBlock = (BYTE*)sAllocMemory (npBufferSize);
    m_pbBufferEnd = m_pbBufferBegin + npBufferSize;

    // 建立链表
    BYTE* pbBlock = m_pbBufferBegin;
    for (INT_P i = 1; i < npNumBlocks; i++, pbBlock += m_npPoolBlockSize)
    {  
        *(BYTE**)pbBlock = pbBlock + m_npPoolBlockSize;
    }

    *(BYTE**)pbBlock = NULL;  // 最后一块的下一块为空块
    ASSERT (pbBlock + m_npPoolBlockSize == m_pbBufferEnd);

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
    m_npNumBlocks = npNumBlocks;
    m_npNumAllocedBlocks = 0;  // 初始化已分配块数目
    m_npNumMaxAllocedBlocks = 0;  // 初始化最多同时分配块数目
    m_npNumTotalAllocTimes = 0;
    m_npNumTotalAllocedInCacheTimes = 0;
#endif
}

CPoolMem::~CPoolMem ()
{
    ASSERT (m_pbBufferBegin != NULL);

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
    DEC_INTP_VAR_A (s_npNumAllocedMemories)  // 提前减去后面即将调用sFreeMemory释放的内存块

    TCHAR buf [256];
    if (s_npNumAllocedMemories != 0)
    {
        _stprintf (buf, _T_VOL_DEBUG_OUT_STRING_LEADER _T_MEMORY_LEAK_REPORT_D, s_npNumAllocedMemories);
        DEBUG_PRINT (buf);
    }

    DumpReport ();
#endif

    sFreeMemory (m_pbBufferBegin);  // 释放所分配的内存池
}

void* CPoolMem::Alloc (const INT_P npSize)
{
    void* p = AllocMaybeRetNull (npSize);
    if (p == NULL)
    {
        FAIL;
        exit (-1);  // 分配失败则退出程序
    }

    return p;
}

void* CPoolMem::Realloc (const void* p, const INT_P npNewSize)
{
    void* pNew = ReallocMaybeRetNull (p, npNewSize);
    if (pNew == NULL)
    {
        FAIL;
        exit (-1);  // 重分配失败则退出程序
    }

    return pNew;
}

void* CPoolMem::AllocMaybeRetNull (const INT_P npSize)
{
    ASSERT (npSize > 0);

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
    // 总共分配内存的次数加1
    #ifdef _PF_WIN32
        _asm mov eax, [this]
        _asm lock inc dword ptr [eax + m_npNumTotalAllocTimes]
    #else
        INC_INTP_VAR_A (m_npNumTotalAllocTimes);
    #endif
#endif

    if (npSize > m_npPoolBlockSize)  // 超出单个块尺寸?
    {
        return sAllocMemoryMaybeRetNull (npSize);  // 直接分配
    }
    else
    {
        m_locker.lock ();

        // 从内存池中分配内存时,直接将链首返回给调用者,同时将链首指向的下一块指定为新的链首.
        void* pBlock = m_pbCurrentBlock;  // 获得当前块
        if (pBlock != NULL)  // 尚有缓存块未被使用?
        {
            m_pbCurrentBlock = *(BYTE**)m_pbCurrentBlock;  // 到下一块
        #ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
            m_npNumTotalAllocedInCacheTimes++;  // 总共在内存池中分配内存的次数加1
            m_npNumAllocedBlocks++;  // 已分配块数目加1
            if (m_npNumAllocedBlocks > m_npNumMaxAllocedBlocks)
                m_npNumMaxAllocedBlocks = m_npNumAllocedBlocks;
        #endif
        }
    #ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
        else
        {
            // 此时必定所有的块都已经被分配出去
            ASSERT (m_npNumAllocedBlocks == (m_pbBufferEnd - m_pbBufferBegin) / m_npPoolBlockSize);
        }
    #endif

        m_locker.unlock ();

        if (pBlock == NULL)  // 所有缓存块均被使用?
            return sAllocMemoryMaybeRetNull (npSize);  // 直接分配

        ASSERT ((BYTE*)pBlock >= m_pbBufferBegin && (BYTE*)pBlock < m_pbBufferEnd &&
                (((BYTE*)pBlock - m_pbBufferBegin) % m_npPoolBlockSize) == 0);  // 必定分配在块首部

        return pBlock;
    }
}

void* CPoolMem::ReallocMaybeRetNull (const void* p, const INT_P npNewSize)
{
    ASSERT (p != NULL && npNewSize > 0);

    if ((const BYTE*)p < m_pbBufferBegin || (const BYTE*)p >= m_pbBufferEnd)  // 该块在内存池外部?
    {
        return sReallocMemoryMaybeRetNull (p, npNewSize);
    }
    else  // 该块在内存池内部
    {
        ASSERT ((((const BYTE*)p - m_pbBufferBegin) % m_npPoolBlockSize) == 0);  // 必定分配在块首部

        if (npNewSize <= m_npPoolBlockSize)  // 调整后的尺寸在单个块尺寸内?
            return (void*)p;  // 直接返回

        void* pNew = sAllocMemoryMaybeRetNull (npNewSize);  // 直接分配内存
        if (pNew == NULL)
            return NULL;

         // 由于p在内存池内部,所以p所指向数据的尺寸必定小于等于缓存块尺寸,所以此处拷贝整个块内容即可.
        ASSERT (npNewSize > m_npPoolBlockSize);  // 前面检查过
        COPY_MEM (pNew, p, m_npPoolBlockSize);
        
        //-----------------------  释放原内存

        m_locker.lock ();

        // 释放时将要释放的块指定为新的链首,并指向原链首即可.
        *(BYTE**)p = (BYTE*)m_pbCurrentBlock;
        m_pbCurrentBlock = (BYTE*)p;

    #ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
        m_npNumAllocedBlocks--;  // 已分配块数目减1
    #endif

        m_locker.unlock ();
        return pNew;
    }
}

void CPoolMem::Free (const void* p)
{  
    ASSERT (p != NULL);

    if ((const BYTE*)p < m_pbBufferBegin || (const BYTE*)p >= m_pbBufferEnd)  // 在内存池外部?
    {
        sFreeMemory (p);  // 直接释放
    }
    else
    {
        ASSERT ((((const BYTE*)p - m_pbBufferBegin) % m_npPoolBlockSize) == 0);  // 必定分配在块首部

        m_locker.lock ();

        // 释放时将要释放的块指定为新的链首,并指向原链首即可.
        *(BYTE**)p = (BYTE*)m_pbCurrentBlock;
        m_pbCurrentBlock = (BYTE*)p;

    #ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?
        m_npNumAllocedBlocks--;  // 已分配块数目减1
    #endif

        m_locker.unlock ();
    }
}  

#ifdef _VOL_POOL_MEMORY_LEAKS_CHECK_ENABLED  // 需要检查内存垃圾?

void CPoolMem::DumpReport () const
{
    TCHAR buf [512];
    _stprintf (buf, _T_VOL_DEBUG_OUT_STRING_LEADER _T_MEMORY_LEAK_REPORT_DDDDF,
            m_npNumMaxAllocedBlocks, m_npNumBlocks, m_npNumTotalAllocTimes, m_npNumTotalAllocedInCacheTimes,
            (m_npNumTotalAllocTimes == 0 ? 0.0f : (FLOAT)m_npNumTotalAllocedInCacheTimes * 100.0f / (FLOAT)m_npNumTotalAllocTimes));

    DEBUG_PRINT (buf);
}

#endif

//-------------------------------------------------------------------------------

CBlockPoolMem::CBlockPoolMem (const INT_P npBlockSize, const INT_P npNumBlocksInRegion, const REGION_SHRINK_MODE enShrinkMode)
{
    m_enShrinkMode = enShrinkMode;
    _init (npBlockSize, npNumBlocksInRegion);
}

void CBlockPoolMem::Reset (const INT_P npBlockSize, const INT_P npNumBlocksInRegion)
{
    FreeAll ();

    _init ((npBlockSize == -1 ? m_npBlockSize : npBlockSize),
            (npNumBlocksInRegion == -1 ? m_npNumBlocksInRegion : npNumBlocksInRegion));
}

void CBlockPoolMem::_init (const INT_P npBlockSize, const INT_P npNumBlocksInRegion)
{
    ASSERT (npBlockSize > 0 && npNumBlocksInRegion > 0);

    m_pFirstRegion = NULL;
    m_npNumBlocksInRegion = MAX (32, npNumBlocksInRegion);
    m_npBlockSize = MAX ((INT_P)sizeof (void*), npBlockSize);  // 块尺寸必须至少能保存一个指针
    m_npRegionSize = m_npBlockSize * m_npNumBlocksInRegion;
}

CBlockPoolMem::~CBlockPoolMem ()
{
    FreeAll ();
}

void* CBlockPoolMem::AllocBlock ()
{
    POOL_REGION_HEADER* pRegion = m_pFirstRegion;

    while (TRUE)
    {
        if (pRegion == NULL)  // 所有区域均已经被使用?
        {
            // 分配一个新区域
            pRegion = (POOL_REGION_HEADER*)sAllocMemory (sizeof (POOL_REGION_HEADER) + m_npRegionSize);
            pRegion->m_pbCurrentBlock = (BYTE*)(pRegion + 1);
            pRegion->m_npNumAllocedBlocks = 0;
            pRegion->m_pNextRegion = m_pFirstRegion;
            m_pFirstRegion = pRegion;  // 设置为区域链表首

            // 建立区域内块链表
            BYTE* pbBlock = pRegion->m_pbCurrentBlock;
            for (INT_P i = 1; i < m_npNumBlocksInRegion; i++, pbBlock += m_npBlockSize)
            {  
                *(BYTE**)pbBlock = pbBlock + m_npBlockSize;
            }
            *(BYTE**)pbBlock = NULL;  // 最后一块的下一块为空块
            ASSERT (pbBlock + m_npBlockSize == (BYTE*)(pRegion + 1) + m_npRegionSize);
        }

        //-----------------------------------------  在当前区域内尝试分配

        ASSERT (pRegion != NULL);  // 为NULL时前面已经处理过了

        if (pRegion->m_pbCurrentBlock != NULL)  // 存在空闲块?
        {
            ASSERT (pRegion->m_npNumAllocedBlocks < m_npNumBlocksInRegion);  // 必定存在没有被分配出去的块

            // 从内存池中分配内存时,直接将链首返回给调用者,同时将链首指向的下一块指定为新的链首.
            void* pBlock = pRegion->m_pbCurrentBlock;  // 获得当前块
            pRegion->m_pbCurrentBlock = *(BYTE**)pBlock;  // 到下一块
            pRegion->m_npNumAllocedBlocks++;  // 区域内已分配块数目加1

            return pBlock;
        }
    #ifdef _DEBUG
        else
            ASSERT (pRegion->m_npNumAllocedBlocks == m_npNumBlocksInRegion);  // 所有块都必须已经被分配出去
    #endif

        //-----------------------------------------  到下一区域

        pRegion = pRegion->m_pNextRegion;
    }
}

INT_P CBlockPoolMem::CalcNumAllocedBlocks () const
{
    INT_P npNumAllocedBlocks = 0;

    const POOL_REGION_HEADER* pRegion = m_pFirstRegion;
    while (pRegion != NULL)
    {
        npNumAllocedBlocks += pRegion->m_npNumAllocedBlocks;
        pRegion = pRegion->m_pNextRegion;
    }

    return npNumAllocedBlocks;
}

BOOL_P CBlockPoolMem::IsValid (const void* p)
{
    ASSERT (p != NULL);

    // 寻找所处区域和所处内存块
    const POOL_REGION_HEADER* pRegion = m_pFirstRegion;
    while (pRegion != NULL)
    {
        const BYTE* pData = (const BYTE*)(pRegion + 1);  // 获得区域的内存块部分
        if (p >= pData && p < pData + m_npRegionSize)  // 找到了?
            return TRUE;

        pRegion = pRegion->m_pNextRegion;
    }

    return FALSE;
}

void CBlockPoolMem::FreeBlock (const void* pBlock)
{
    ASSERT (pBlock != NULL);

    POOL_REGION_HEADER* pRegion = m_pFirstRegion;
    while (pRegion != NULL)
    {
        const BYTE* pData = (const BYTE*)(pRegion + 1);  // 获得区域的内存块部分

        if (pBlock < pData || pBlock >= pData + m_npRegionSize)  // 不在此区域内部?
        {
            pRegion = pRegion->m_pNextRegion;  // 到下一区域
        }
        else
        {
            ASSERT ((((BYTE*)pBlock - pData) % m_npBlockSize) == 0 &&  // 必定分配在块首部
                    pRegion->m_npNumAllocedBlocks > 0);  // 区域内已分配块数目必定大于0

            // 释放时将要释放的块指定为新的链首,并指向原链首即可.
            *(BYTE**)pBlock = (BYTE*)pRegion->m_pbCurrentBlock;
            pRegion->m_pbCurrentBlock = (BYTE*)pBlock;

            pRegion->m_npNumAllocedBlocks--;  // 区域内已分配块数目减1

            //-----------------------------------------------

            // 整个区域都没有被使用了?
            if (pRegion->m_npNumAllocedBlocks == 0 &&
                    m_enShrinkMode != RSM_KEEP_ALL)  // 不为保留所有区域?
            {
                // 释放该区域
                if (pRegion == m_pFirstRegion)  // 为首区域?
                {
                    if (m_enShrinkMode == RSM_KEEP_NONE ||  // 不保留任何区域?
                            pRegion->m_pNextRegion != NULL)  // 首区域不为唯一剩下的区域?
                    {
                        m_pFirstRegion = pRegion->m_pNextRegion;
                        sFreeMemory (pRegion);
                    }
                }
                else  // 释放非首区域
                {
                    POOL_REGION_HEADER* pRegion2 = m_pFirstRegion;

                    while (pRegion2 != NULL)
                    {
                        if (pRegion2->m_pNextRegion == pRegion)
                        {
                            pRegion2->m_pNextRegion = pRegion->m_pNextRegion;
                            break;
                        }
                        pRegion2 = pRegion2->m_pNextRegion;
                    }
                    ASSERT (pRegion2 != NULL);  // 必定能够找到

                    sFreeMemory (pRegion);
                }
            }

            return;
        }
    }

    FAIL;  // 说明欲释放的指针无效
}

void CBlockPoolMem::FreeAll ()
{
    const POOL_REGION_HEADER* pRegion = m_pFirstRegion;
    while (pRegion != NULL)
    {
        const POOL_REGION_HEADER* pNextRegion = pRegion->m_pNextRegion;
        sFreeMemory ((void*)pRegion);
        pRegion = pNextRegion;
    }

    m_pFirstRegion = NULL;
}
