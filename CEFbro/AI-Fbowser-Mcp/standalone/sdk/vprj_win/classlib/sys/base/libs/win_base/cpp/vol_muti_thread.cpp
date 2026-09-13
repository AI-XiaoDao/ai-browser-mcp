
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

#ifdef _PF_LINUX

BOOL_P CMSemaphore::wait_timeout (const INT_P npMillseconds) const
{
    ASSERT (npMillseconds >= 0);

    // 获得当前时间
    timeval tv;
    ::gettimeofday (&tv, NULL);

    // 转换到timespec
    timespec ts;
    ts.tv_sec = tv.tv_sec;
    ts.tv_nsec = tv.tv_usec * 1000 + npMillseconds * 1000 * 1000;

    // 规范化时间值
    ts.tv_sec += ts.tv_nsec / (1000 * 1000 * 1000);
    ts.tv_nsec %= (1000 * 1000 * 1000);

    // 等待信号灯置位.注意:此调用可能被信号中断,所以实际等待时间并不一定是所指定的等待时间.
    return (sem_timedwait ((sem_t*)&m_sem, &ts) == 0);
}

#endif

//----------------------------------------------------------------

BOOL_P VolBeginThread (LPTHREAD_START_ROUTINE fnThread, const INT_P npUserParam,
        const INT_P npStackSize, const INT_P npPriority, const BOOL_P blpWaitThreadExit)
{
    ASSERT (fnThread != NULL);

    DWORD idThread;
    const HANDLE hThread = ::CreateThread (NULL, (SIZE_T)npStackSize, fnThread, (LPVOID)npUserParam, 0, &idThread);
    if (hThread == NULL)
        return FALSE;

    if (npPriority != THREAD_PRIORITY_NORMAL)
        ::SetThreadPriority (hThread, (INT)npPriority);

    if (blpWaitThreadExit)
        ::WaitForSingleObject (hThread, INFINITE);

    VERIFY (::CloseHandle (hThread));
    return TRUE;
}

CVolThreadState::CVolThreadState ()
{
    m_hEventNeedExit =  ::CreateEvent (NULL, TRUE, FALSE, NULL);
    m_hEventExited =  ::CreateEvent (NULL, TRUE, TRUE, NULL);

    ZERO_MEM (m_apUserVolObjects, sizeof (m_apUserVolObjects));
    m_npUserData = 0;
}

CVolThreadState::~CVolThreadState ()
{
    VERIFY (::CloseHandle (m_hEventNeedExit));
    VERIFY (::CloseHandle (m_hEventExited));

    for (INT_P npIndex = 0; npIndex < NUM_ELEMENTS_OF (m_apUserVolObjects); npIndex++)
    {
        if (m_apUserVolObjects [npIndex] != NULL)
            m_apUserVolObjects [npIndex]->Destroy ();
    }
}

void CVolThreadState::Reset ()
{
    ::ResetEvent (m_hEventNeedExit);
    ::ResetEvent (m_hEventExited);
}

void CVolThreadState::SetUserVolObjectPtr (const INT_P npIndex, const CVolObject* pObject)
{
    ASSERT (npIndex >= 0 && npIndex < NUM_ELEMENTS_OF (m_apUserVolObjects));

    CVolObject* pNewUserVolObject = (pObject == NULL ? NULL : pObject->MakeCloneObject ());

    m_lockerUserVolObject.lock ();
    CVolObject* pOldUserVolObject = m_apUserVolObjects [npIndex];
    m_apUserVolObjects [npIndex] = pNewUserVolObject;
    m_lockerUserVolObject.unlock ();

    if (pOldUserVolObject != NULL)
        pOldUserVolObject->Destroy ();
}

BOOL_P CVolThreadState::GetUserVolObject (const INT_P npIndex, CVolObject& obj) const
{
    ASSERT (npIndex >= 0 && npIndex < NUM_ELEMENTS_OF (m_apUserVolObjects));

    CMutexLocker locker (m_lockerUserVolObject);
    return (m_apUserVolObjects [npIndex] == NULL ? FALSE : obj.CheckCopyFrom (*m_apUserVolObjects [npIndex]));
}

//----------------------------------------------------------------

void CVolThread::Exit ()
{
    if (m_blpRunning)  // 线程正在运行?
    {
        PostExitNotify ();  // 发出退出通知

        while (m_blpRunning)  // 等待线程退出
            MSleep (10);
    }

#if defined (_PF_WINDOWS)
    if (m_handle != NULL)
    {
        VERIFY (::CloseHandle (m_handle));
        m_handle = NULL;
    }
    m_idThread = 0;
#endif

    m_blpExit = FALSE;
    ASSERT (m_blpRunning == FALSE);
}

void CVolThread::PostExitNotify ()
{
    if (m_blpRunning)  // 线程正在运行?
    {
        // 发出退出通知
    #if defined (_PF_WINDOWS)
        m_evExit.post ();
    #endif
        m_blpExit = TRUE;  // 设置线程处于等待退出状态
    }
}

BOOL_P CVolThread::IsNeedExit (INT_P npMillseconds) const
{
    if (m_blpExit)  // 已经得到了通知?
        return TRUE;

    if (npMillseconds == 0)  // 不等待?
        return m_blpExit;

    if (npMillseconds < 0)  // 一直等待?
    {
    #if defined (_PF_WINDOWS)
        return m_evExit.wait ();
    #else
        while (m_blpExit == FALSE)
            MSleep (10);
        return m_blpExit;
    #endif
    }

#if defined (_PF_WINDOWS)
    return m_evExit.wait_timeout (npMillseconds);
#else
    while (m_blpExit == FALSE && npMillseconds > 0)
    {
        MSleep (10);
        npMillseconds -= 10;
    }
    return m_blpExit;
#endif
}

#if defined (_PF_WINDOWS)
    DWORD WINAPI CVolThread::sThreadCallOther (CVolThread* pThread)
#elif defined (_PF_LINUX)
    void* CVolThread::sThreadCallOther (CVolThread* pThread)
#endif
    {
        ASSERT (pThread != NULL && pThread->m_fnThreadMain != NULL);
    #if defined (_PF_WINDOWS)
        pThread->m_fnThreadMain (pThread->m_pmThread, &pThread->m_blpExit, pThread->m_evExit.GetHandle ());
        pThread->m_blpRunning = FALSE;  // 设置线程已经退出
        pThread->thOnThreadRunOver ();
        return 0;
    #elif defined (_PF_LINUX)
        pThread->m_fnThreadMain (pThread->m_pmThread, &pThread->m_blpExit, NULL);
        pThread->m_blpRunning = FALSE;  // 设置线程已经退出
        pthread_exit (NULL);
        pThread->thOnThreadRunOver ();
        return NULL;
    #endif
    }

#if defined (_PF_WINDOWS)
    DWORD WINAPI CVolThread::sThreadCallSelf (CVolThread* pThread)
#elif defined (_PF_LINUX)
    void* CVolThread::sThreadCallSelf (CVolThread* pThread)
#endif
    {
        ASSERT (pThread != NULL);
        pThread->main (pThread->m_pmThread);
        pThread->m_blpRunning = FALSE;  // 设置线程已经退出
    #if defined (_PF_WINDOWS)
        pThread->thOnThreadRunOver ();
        return 0;
    #elif defined (_PF_LINUX)
        pthread_exit (NULL);
        pThread->thOnThreadRunOver ();
        return NULL;
    #endif
    }

// 注意Start方法只能在单一线程中运行
BOOL_P CVolThread::Start (const VOL_THREAD_FUNC fnThreadMain, void* param, const INT_P npStackSize)
{
    ASSERT (npStackSize >= 0);

    if (m_blpRunning)  // 正在运行?
        return TRUE;  // 直接返回
    m_blpRunning = TRUE;  // 设置线程正在运行标志

#if defined (_PF_WINDOWS)
    if (m_handle != NULL)
        VERIFY (::CloseHandle (m_handle));
    m_evExit.reset ();  // 重置退出通知事件
#endif
    m_blpExit = FALSE;

    m_fnThreadMain = fnThreadMain;
    m_pmThread = param;

#if defined (_PF_WINDOWS)

    m_handle = ::CreateThread (NULL, (SIZE_T)npStackSize,
            (fnThreadMain == NULL ? (LPTHREAD_START_ROUTINE)sThreadCallSelf : (LPTHREAD_START_ROUTINE)sThreadCallOther),
            this, 0, &m_idThread);
    if (m_handle == NULL)
    {
        m_blpRunning = FALSE;
        return FALSE;
    }

#elif defined (_PF_LINUX)

    pthread_attr_t attr;
    pthread_attr_init (&attr);
    if (npStackSize > 0)
        pthread_attr_setstacksize (&attr, npStackSize);

    pthread_t idThread;
    INT nResult = pthread_create (&idThread, &attr,
            (fnThreadMain == NULL ? (void*(*)(void*))sThreadCallSelf : (void*(*)(void*))sThreadCallOther),
            this);

    pthread_attr_destroy (&attr);

    if (nResult != 0)  // 启动失败?
    {
        m_blpRunning = FALSE;
        return FALSE;
    }

    VERIFY_EQUAL (pthread_detach (idThread), 0);

#else
    #error unsupported platform.
#endif

    return TRUE;
}

//----------------------------------------------------------------

#if defined (_PF_WINDOWS)

#define VPTS_NONE       0  // 尚未开始运行或已经运行结束
#define VPTS_RUNNING    1  // 正在运行
#define VPTS_IDLE       2  // 正在空闲等待重启
#define _VPTS_CONTINUE  3  // 正在等待重启后继续执行. 注意本状态是一个很短暂的内部状态,不需要对其进行处理.

CVolPoolThread::CVolPoolThread ()
{
    m_hVolThread = 0;
    m_blpExitThread = FALSE;
    m_blpBreak = FALSE;
    m_upIdleBeginTime = 0;
    m_npState = VPTS_NONE;

    m_fnThreadMain = NULL;
    m_upParam1 = m_upParam2 = 0;
}

void CVolPoolThread::ResetAllEvents ()
{
    CMutexLocker locker (m_mxThread);

    m_blpExitThread = FALSE;
    m_blpBreak = FALSE;

    m_evBreak.reset ();
    m_evIdle.reset ();
    m_evContinue.reset ();
}

void CVolPoolThread::Exit ()
{
    m_mxThread.lock ();

    if (m_npState != VPTS_NONE)  // 线程不处于初始或停止状态?
    {
        // 发出退出通知
        m_blpExitThread = TRUE;
        m_blpBreak = TRUE;
        m_evBreak.post ();
        m_evIdle.post ();
        m_evContinue.post ();

        m_mxThread.unlock ();

        while (m_npState != VPTS_NONE)  // 等待线程退出
            MSleep (10);

        ResetAllEvents ();
    }
    else
    {
        m_mxThread.unlock ();
    }
}

void CVolPoolThread::BreakToIdle ()
{
    m_mxThread.lock ();

    if (m_npState == VPTS_RUNNING)
    {
        // 发出退出通知
        ASSERT (m_blpExitThread == FALSE);
        m_blpBreak = TRUE;
        m_evBreak.post ();
        m_evIdle.reset ();
        m_evContinue.post ();

        m_mxThread.unlock ();

        while (m_npState != VPTS_NONE && m_npState != VPTS_IDLE)  // 等待线程退出或进入空闲状态
            MSleep (10);

        ResetAllEvents ();
    }
    else
    {
        ASSERT (m_npState == VPTS_NONE || m_npState == VPTS_IDLE);  // 唯一剩余的可能
        m_mxThread.unlock ();
    }
}

BOOL_P CVolPoolThread::IsIdle (UINT_P* pupIdleBeginTime) const
{
    CMutexLocker locker (m_mxThread);

    if (pupIdleBeginTime != NULL)
        *pupIdleBeginTime = m_upIdleBeginTime;
    return (m_npState == VPTS_IDLE);
}

BOOL_P CVolPoolThread::IsRunning () const
{
    CMutexLocker locker (m_mxThread);

    return (m_npState == VPTS_RUNNING);
}

BOOL_P CVolPoolThread::SafeIsNeedBreak () const
{
    if (this == NULL)  // 对象为NULL?
        return TRUE;  // 默认返回需要退出

    CMutexLocker locker (m_mxThread);
    return m_blpBreak;
}

BOOL_P CVolPoolThread::Start (VOL_POOL_THREAD_FUNC fnThreadMain, UINT_P upParam1, UINT_P upParam2, HVOLTHREAD hAllocedVolThread)
{
    ASSERT (fnThreadMain != NULL && hAllocedVolThread != 0);  // 进入本方法的前提

    m_mxThread.lock ();

    if (m_npState == VPTS_IDLE)  // 处于空闲等待重启状态?
    {
        m_hVolThread = hAllocedVolThread;
        m_fnThreadMain = fnThreadMain;
        m_upParam1 = upParam1;
        m_upParam2 = upParam2;

        m_blpExitThread = FALSE;
        m_blpBreak = FALSE;
        m_evBreak.reset ();
        m_evContinue.reset ();
        m_evIdle.post ();

        m_mxThread.unlock ();

        while (m_npState == VPTS_IDLE)
            MSleep (10);
        ASSERT (m_npState == _VPTS_CONTINUE);  // 正常情况下必定为此状态

        m_evBreak.reset ();
        m_evIdle.reset ();
        m_evContinue.post ();

        while (m_npState == _VPTS_CONTINUE)
            MSleep (10);
        ASSERT (m_npState == VPTS_RUNNING || m_npState == VPTS_IDLE);  // 正常情况下必定为这两种状态

        m_evContinue.reset ();
    }
    else
    {
        m_mxThread.unlock ();

        if (m_npState == VPTS_RUNNING)  // 已经正在运行?
            return FALSE;
        ASSERT (m_npState == VPTS_NONE);  // 唯一剩余的可能

        ResetAllEvents ();
        ASSERT (m_fnThreadMain == NULL);
        m_fnThreadMain = fnThreadMain;
        m_upParam1 = upParam1;
        m_upParam2 = upParam2;

        const HVOLTHREAD hBak = m_hVolThread;
        m_hVolThread = hAllocedVolThread;

        ASSERT (m_blpExitThread == FALSE);  // 前面重置了
        DWORD idThread;
        const HANDLE hWinThread = ::CreateThread (NULL, 0, (LPTHREAD_START_ROUTINE)CVolPoolThread::sThreadMain, this, 0, &idThread);
        if (hWinThread == NULL)
        {
            m_fnThreadMain = NULL;
            m_hVolThread = hBak;
            return FALSE;
        }
        VERIFY (::CloseHandle (hWinThread));

        // 等待线程进入运行或空闲状态
        while (m_npState == VPTS_NONE)
            MSleep (10);
        ASSERT (m_npState == VPTS_RUNNING || m_npState == VPTS_IDLE);  // 正常情况下必定为这两种状态
    }

    return TRUE;
}

DWORD WINAPI CVolPoolThread::sThreadMain (LPVOID lpThreadParameter)
{
    ASSERT (lpThreadParameter != NULL);
    return ((CVolPoolThread*)lpThreadParameter)->main ();
}

DWORD CVolPoolThread::main ()
{
    while (TRUE)
    {
        m_mxThread.lock ();

        const HVOLTHREAD hVolThread = m_hVolThread;
        VOL_POOL_THREAD_FUNC fnThreadMain = m_fnThreadMain;
        UINT_P upParam1 = m_upParam1;
        UINT_P upParam2 = m_upParam2;

        m_fnThreadMain = NULL;

        if (m_blpExitThread)
        {
            m_mxThread.unlock ();
            break;
        }

        m_npState = VPTS_RUNNING;
        m_mxThread.unlock ();

        if (fnThreadMain != NULL)
            fnThreadMain (hVolThread, upParam1, upParam2, m_evBreak.GetHandle ());

        //----------------------------------------------------------------

        m_mxThread.lock ();
        m_npState = VPTS_IDLE;  // 设置进入了空闲状态
        m_upIdleBeginTime = ::MGetTickCount ();  // 记录进入空闲时间
        m_mxThread.unlock ();

        m_evIdle.wait ();

        //----------------------------------------------------------------

        m_mxThread.lock ();
        m_npState = _VPTS_CONTINUE;  // 设置进入了等待继续执行状态
        m_upIdleBeginTime = 0;
        m_mxThread.unlock ();

        m_evContinue.wait ();
    }

    m_npState = VPTS_NONE;
    return 0;
}

//----------------------------------------------------------------

#define DEFAULT_MAX_THREAD_IDLE_INTERVAL  (16 * 1000)

CVolThreadPool::CVolThreadPool (const INT_P npPoolUpdateInterval) :
        m_npPoolUpdateInterval (MAX (500, npPoolUpdateInterval)),
        m_arypThreads (32)
{
    m_npMaxNumIdleThreads = GetRecommendWorkingThreadCount (0);
    m_npMaxThreadIdleInterval = DEFAULT_MAX_THREAD_IDLE_INTERVAL;
    m_upFreeThreadID = 1;
    m_upLastUpdateTime = 0;
}

void CVolThreadPool::Cleanup ()
{
    m_mxPool.lock ();

    m_upFreeThreadID = 1;
    m_upLastUpdateTime = 0;

    CVolPoolThreadArray arypThreads;
    arypThreads.Copy (m_arypThreads);
    m_arypThreads.RemoveAll ();

    m_mxPool.unlock ();

    const INT_P npNumThreads = arypThreads.GetCount ();
    for (INT_P npIndex = 0; npIndex < npNumThreads; npIndex++)
        arypThreads [npIndex]->Destroy ();
}

void CVolThreadPool::SetMaxNumIdleThreads (const INT_P npMaxNumIdleThreads)
{
    m_mxPool.lock ();
    m_npMaxNumIdleThreads = (npMaxNumIdleThreads <= 0 ? GetRecommendWorkingThreadCount (0) : npMaxNumIdleThreads);
    m_mxPool.unlock ();

    UpdatePool (TRUE);
}

void CVolThreadPool::SetMaxThreadIdleInterval (const INT_P npMaxThreadIdleInterval)
{
    m_mxPool.lock ();
    m_npMaxThreadIdleInterval = (npMaxThreadIdleInterval <= 0 ? DEFAULT_MAX_THREAD_IDLE_INTERVAL : npMaxThreadIdleInterval);
    m_mxPool.unlock ();

    UpdatePool (TRUE);
}

// 进入本方法前必需首先加锁m_mxPool
CVolPoolThread* CVolThreadPool::_FindThread (HVOLTHREAD hVolThread) const
{
    if (hVolThread == NULL)
        return NULL;

    const INT_P npNumThreads = m_arypThreads.GetCount ();
    for (INT_P npIndex = 0; npIndex < npNumThreads; npIndex++)
    {
        if (m_arypThreads [npIndex]->GetHandle () == hVolThread)
            return m_arypThreads [npIndex];
    }

    return NULL;
}

// 进入本方法前必需首先加锁m_mxPool
HVOLTHREAD CVolThreadPool::_AllocThreadHandle ()
{
    HVOLTHREAD hVolThread = (HVOLTHREAD)m_upFreeThreadID++;
    if (hVolThread == 0)
        hVolThread = (HVOLTHREAD)m_upFreeThreadID++;

    return hVolThread;
}

#if defined (_DEBUG) && defined (_TRACE_VOL_THREAD_POOL)
    #define VOLPOOL_TRACE0(s)  TRACE0(s)
    #define VOLPOOL_TRACE1(fmt,s1)  TRACE1(fmt,s1)
    #define VOLPOOL_TRACE2(fmt,s1,s2)  TRACE2(fmt,s1,s2)
#else
    #define VOLPOOL_TRACE0(s)
    #define VOLPOOL_TRACE1(fmt,s1)
    #define VOLPOOL_TRACE2(fmt,s1,s2)
#endif

HVOLTHREAD CVolThreadPool::StartNewThread (VOL_POOL_THREAD_FUNC fnThreadMain, UINT_P upParam1, UINT_P upParam2)
{
    UpdatePool (TRUE);

    if (fnThreadMain == NULL)  // 未提供用户线程函数?
        return NULL;

    CVolPoolThreadArray arypThreads;
    m_mxPool.lock ();

    const HVOLTHREAD hVolThread = _AllocThreadHandle ();  // 分配一个线程句柄值
    arypThreads.Copy (m_arypThreads);

    m_mxPool.unlock ();

    //--------------------------------------------------  尝试启动所找到的空闲线程

    INT_P npNumThreads = arypThreads.GetCount (), npIndex;

    for (npIndex = 0; npIndex < npNumThreads; npIndex++)
    {
        CVolPoolThread* pPoolThread = arypThreads [npIndex];

        if (pPoolThread->GetState () != VPTS_RUNNING &&  // 处于空闲或结束状态?
                pPoolThread->Start (fnThreadMain, upParam1, upParam2, hVolThread))  // 启动成功?
        {
            VOLPOOL_TRACE1 (_T_VTP_START_NEW_THREAD_FROM_POOL_SUCCEEDED_D, (INT)hVolThread);
            return hVolThread;
        }
    }

    //--------------------------------------------------  否则创建一个新线程

    CVolPoolThread* pPoolThread = new CVolPoolThread;
    m_mxPool.lock ();
    npIndex = m_arypThreads.Add2 (pPoolThread);  // 必须首先加入记录,不然线程中可能会找不到.
    m_mxPool.unlock ();

    if (pPoolThread->Start (fnThreadMain, upParam1, upParam2, hVolThread) == FALSE)
    {
        VOLPOOL_TRACE0 (_T_VTP_START_NEW_THREAD_FAIL);

        m_mxPool.lock ();
        ASSERT (m_arypThreads.GetAt (npIndex) == pPoolThread);  // 唯一的多线程并行代码 IsThreadNeedBreak 中不会修改线程池中的线程列表.
        m_arypThreads.RemoveAt (npIndex);
        m_mxPool.unlock ();

        pPoolThread->Destroy ();
        return NULL;
    }

    VOLPOOL_TRACE1 (_T_VTP_CREATE_AND_START_NEW_THREAD_SUCCEEDED_D, (INT)hVolThread);
    return hVolThread;
}

// 注意本方法将在被启动的线程中执行
BOOL_P CVolThreadPool::IsThreadNeedBreak (HVOLTHREAD hVolThread, INT_P npMillseconds) const
{
    if (hVolThread == NULL)
        return NULL;

    m_mxPool.lock ();
    BOOL_P blpNeedBreak = TRUE;

    do
    {
        CVolPoolThread* pPoolThread = _FindThread (hVolThread);
        if (pPoolThread->SafeIsNeedBreak ())
            break;
        ASSERT (pPoolThread != NULL);

        if (npMillseconds == 0)  // 不等待?
        {
            blpNeedBreak = FALSE;
            break;
        }

        const HANDLE hBreakEvent = pPoolThread->GetBreakEventHandle ();
        ASSERT (hBreakEvent != NULL);

        m_mxPool.unlock ();

        //----------------------------  下面的代码必须处理hVolThread随时可能失效的情况

        if (npMillseconds < 0)  // 一直等待?
        {
            ASSERT (blpNeedBreak);  // 必定为前面的初始值

            while (TRUE)
            {
                ::WaitForSingleObject (hBreakEvent, INFINITE);

                m_mxPool.lock ();
                if (_FindThread (hVolThread)->SafeIsNeedBreak ())
                    break;
                m_mxPool.unlock ();
            }
        }
        else
        {
            ::WaitForSingleObject (hBreakEvent, (DWORD)npMillseconds);

            m_mxPool.lock ();
            blpNeedBreak = _FindThread (hVolThread)->SafeIsNeedBreak ();
        }
    }
    while (FALSE);

    m_mxPool.unlock ();
    return blpNeedBreak;
}

BOOL_P CVolThreadPool::IsThreadRunning (HVOLTHREAD hVolThread) const
{
    CMutexLocker locker (m_mxPool);

    CVolPoolThread* pPoolThread = _FindThread (hVolThread);
    if (pPoolThread == NULL)
        return FALSE;

    return pPoolThread->IsRunning ();
}

void CVolThreadPool::StopThread (HVOLTHREAD hVolThread)
{
    UpdatePool (TRUE);

    m_mxPool.lock ();
    CVolPoolThread* pPoolThread = _FindThread (hVolThread);
    m_mxPool.unlock ();

    if (pPoolThread != NULL)  // 唯一的多线程并行代码 IsThreadNeedBreak 中不会销毁已有的线程对象.
    {
        pPoolThread->BreakToIdle ();
        VOLPOOL_TRACE1 (_T_VTP_THREAD_FREE_INTO_IDLE_STATE_D, (INT)pPoolThread->GetHandle ());
    }
}

void CVolThreadPool::UpdatePool (const BOOL_P blpUpdateAtOnce)
{
    const UINT_P upCurrentTime = (UINT_P)::MGetTickCount ();
    CVolPoolThreadArray arypRemoveThreads;

    m_mxPool.lock ();

    if (blpUpdateAtOnce == FALSE &&  // 不为立即更新?
            m_upLastUpdateTime <= upCurrentTime &&  // 检查时间未回卷?
            (INT_P)(upCurrentTime - m_upLastUpdateTime) < m_npPoolUpdateInterval)  // 距离上次检查时间未达到所指定时间?
    {
        m_mxPool.unlock ();
        return;
    }

    m_upLastUpdateTime = upCurrentTime;

    //----------------------------------------------------------------

    // 首先清理空闲时间过久的线程
    INT_P npNumIdleThreads = 0;  // 用作记录清理后剩余的空闲线程数目
    INT_P npNumThreads = m_arypThreads.GetCount (), npIndex;
    for (npIndex = npNumThreads - 1; npIndex >= 0; npIndex--)
    {
        CVolPoolThread* pPoolThread = m_arypThreads [npIndex];

        UINT_P upIdleBeginTime;
        if (pPoolThread->IsIdle (&upIdleBeginTime))
        {
            if (upIdleBeginTime > upCurrentTime ||  // 空闲起始时间回卷?
                    (INT_P)(upCurrentTime - upIdleBeginTime) >= m_npMaxThreadIdleInterval)  // 空闲时间已经超出了所指定时间?
            {
                VOLPOOL_TRACE2 (_T_VTP_TOO_LONG_REST_TIME_THREAD_DESTROIED_DD, (INT)pPoolThread->GetHandle (), (INT)(upCurrentTime - upIdleBeginTime));
                arypRemoveThreads.Add (pPoolThread);
                m_arypThreads.RemoveAt (npIndex);
            }
            else
                npNumIdleThreads++;  // 增加当前所保留的空闲线程数目
        }
        else if (pPoolThread->GetState () == VPTS_NONE)  // 已经运行结束?
        {
            // 对于已经运行结束的线程,没有缓存的价值,直接将其删除.
            VOLPOOL_TRACE1 (_T_VTP_ENDED_THREAD_DESTROIED_D, (INT)pPoolThread->GetHandle ());
            arypRemoveThreads.Add (pPoolThread);
            m_arypThreads.RemoveAt (npIndex);
        }
    }

    // 清理所保存的过多空闲线程
    if (npNumIdleThreads > m_npMaxNumIdleThreads)  // 存在过多的空闲线程?
    {
        npNumThreads = m_arypThreads.GetCount ();

        for (npIndex = npNumThreads - 1; npIndex >= 0; npIndex--)
        {
            CVolPoolThread* pPoolThread = m_arypThreads [npIndex];

            if (pPoolThread->GetState () == VPTS_IDLE)  // 处于空闲状态?
            {
                VOLPOOL_TRACE1 (_T_VTP_TOO_MANY_THREAD_DESTROIED_D, (INT)pPoolThread->GetHandle ());

                arypRemoveThreads.Add (pPoolThread);
                m_arypThreads.RemoveAt (npIndex);

                npNumIdleThreads--;
                if (npNumIdleThreads <= m_npMaxNumIdleThreads)  // 已经去除了足够多的空闲线程?
                    break;
            }
        }
    }

    m_mxPool.unlock ();

    //----------------------------------------------------------------

    npNumThreads = arypRemoveThreads.GetCount ();

    for (INT_P npIndex = 0; npIndex < npNumThreads; npIndex++)
        arypRemoveThreads [npIndex]->Destroy ();
}

CVolString& CVolThreadPool::DebugGetDumpString (CVolString& strDump)
{
#ifdef _DEBUG
    CMutexLocker locker (m_mxPool);

    INT_P npNumRunningThreads = 0;
    INT_P npNumIdleThreads = 0;
    INT_P npNumEndedThreads = 0;

    const INT_P npNumThreads = m_arypThreads.GetCount ();
    for (INT_P npIndex = 0; npIndex < npNumThreads; npIndex++)
    {
        const CVolPoolThread* pPoolThread = m_arypThreads [npIndex];

        switch (pPoolThread->GetState ())
        {
        case VPTS_NONE:  npNumEndedThreads++;  break;
        case VPTS_RUNNING:  npNumRunningThreads++;  break;
        case VPTS_IDLE:  npNumIdleThreads++;  break;
        DEFAULT_FAIL
        }
    }

    strDump.Format (_T_VTP_DUMP_FORMAT_DDDD, (INT)npNumThreads, (INT)npNumIdleThreads, (INT)npNumRunningThreads, (INT)npNumEndedThreads);
#else
    strDump.Empty ();
#endif

    return strDump;
}

//----------------------------------------------------------------

BOOL_P CSimpleCompletionPort::wait (INT_P* pnpParam1, INT_P* pnpParam2, INT* pnParam3, INT nMilliseconds)
{
    DWORD dwNumberOfBytes = 0;
    ULONG_PTR pCompletionKey = NULL;
    LPOVERLAPPED pOverlapped = NULL;

    const BOOL_P blpSucceeded = (m_hCompletionPort != NULL ?
            ::GetQueuedCompletionStatus (m_hCompletionPort, &dwNumberOfBytes, &pCompletionKey, &pOverlapped, (DWORD)nMilliseconds) : FALSE);

    if (pnpParam1 != NULL)
        *pnpParam1 = (INT_P)pCompletionKey;
    if (pnpParam2 != NULL)
        *pnpParam2 = (INT_P)pOverlapped;
    if (pnParam3 != NULL)
        *pnParam3 = (INT)dwNumberOfBytes;

    return blpSucceeded;
}

#endif