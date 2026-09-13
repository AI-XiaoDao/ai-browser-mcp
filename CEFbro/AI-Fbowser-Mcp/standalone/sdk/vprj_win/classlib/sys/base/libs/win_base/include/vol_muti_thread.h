
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_MUTI_THREAD_H__
#define __VOL_MUTI_THREAD_H__

class CMMutex : public CVolCommonBase  // 互斥锁
{
public:
    inline_ CMMutex ()
    {
    #if defined (_PF_WINDOWS)
        ::InitializeCriticalSection (&m_cs);
    #elif defined (_PF_LINUX)
        pthread_mutexattr_t attr;
        pthread_mutexattr_init (&attr);
        pthread_mutexattr_settype (&attr, PTHREAD_MUTEX_RECURSIVE_NP);
        pthread_mutex_init (&m_cs, &attr);
        pthread_mutexattr_destroy (&attr);
    #endif
    }

    inline_ ~CMMutex ()
    {
    #if defined (_PF_WINDOWS)
        ::DeleteCriticalSection (&m_cs);
    #elif defined (_PF_LINUX)
        VERIFY_EQUAL (pthread_mutex_destroy (&m_cs), 0);
    #endif
    }

    // 加锁关键段
    // 如果blpTry为真,则会尝试加锁,如果能够加锁,则锁住关键段后返回真,如果不能则返回假.
    // 如果blpTry为假,则会一直等待,直到能够锁住关键段.
    inline_ BOOL_P lock (const BOOL_P blpTry = FALSE) const
    {
        if (blpTry)
        {
        #if defined (_PF_WINDOWS)
            return ::TryEnterCriticalSection (&m_cs);
        #elif defined (_PF_LINUX)
            return (pthread_mutex_trylock ((pthread_mutex_t*)&m_cs) == 0);
        #endif
        }
        else
        {
        #if defined (_PF_WINDOWS)
            ::EnterCriticalSection (&m_cs);
            return TRUE;
        #elif defined (_PF_LINUX)
            return (pthread_mutex_lock ((pthread_mutex_t*)&m_cs) == 0);
        #endif
        }
    }

    // 解开前面已经锁住的关键段,允许其它线程来加锁此关键段
    inline_ void unlock () const
    {
    #if defined (_PF_WINDOWS)
        ::LeaveCriticalSection (&m_cs);
    #elif defined (_PF_LINUX)
        pthread_mutex_unlock ((pthread_mutex_t*)&m_cs);
    #endif
    }

private:
#if defined (_PF_WINDOWS)
    mutable CRITICAL_SECTION m_cs;
#elif defined (_PF_LINUX)
    pthread_mutex_t m_cs;
#endif
};

class CMutexLocker : public CVolCommonBase
{
public:
    inline_ CMutexLocker (const CMMutex& mutex) : m_mutex (mutex)
    {
        m_mutex.lock ();
    }

    inline_ ~CMutexLocker ()
    {
        m_mutex.unlock ();
    }

private:
    const CMMutex& m_mutex;
};

class CMutexLockerP : public CVolCommonBase
{
public:
    inline_ CMutexLockerP (const CMMutex* pMutex) : m_pMutex (pMutex)
    {
        if (m_pMutex != NULL)
        {
            ASSERT_R_DATA (pMutex);
            m_pMutex->lock ();
        }
    }

    inline_ ~CMutexLockerP ()
    {
        if (m_pMutex != NULL)
            m_pMutex->unlock ();
    }

private:
    const CMMutex* m_pMutex;
};

//-----------------------------------------------------------------------

class CMSemaphore : public CVolCommonBase  // 信号灯
{
public:
    inline_ CMSemaphore (const INT nInitValue = 0)
    {
    #if defined (_PF_WINDOWS)
        m_hSemaphore = ::CreateSemaphore (NULL, nInitValue, LONG_MAX, NULL);
    #elif defined (_PF_LINUX)
        VERIFY_EQUAL (sem_init (&m_sem, 0, nInitValue), 0);
    #endif
    }

#if defined (_PF_WINDOWS)
    inline_ CMSemaphore (const INT nInitValue, const TCHAR* szSemaphoreName)
    {
        ASSERT_R_STR_OR_NULL (szSemaphoreName);
        m_hSemaphore = ::CreateSemaphore (NULL, nInitValue, LONG_MAX, szSemaphoreName);
    }
#endif

    inline_ ~CMSemaphore ()
    {
    #if defined (_PF_WINDOWS)
        ::CloseHandle (m_hSemaphore);
    #elif defined (_PF_LINUX)
        VERIFY_EQUAL (sem_destroy (&m_sem), 0);
    #endif
    }

    // 如果blpTry为真,则只测试下信号灯值,如果值大于0,则将其减1后立即成功返回真,否则立即返回假.
    // 如果blpTry为假,则无限等待直到信号值大于0,然后将其减1返回真.
    inline_ BOOL_P wait (const BOOL_P blpTry = FALSE) const
    {
    #if defined (_PF_WINDOWS)
        return (::WaitForSingleObject (m_hSemaphore, (blpTry ? 0 : INFINITE)) == WAIT_OBJECT_0);
    #elif defined (_PF_LINUX)
        if (blpTry)
            return (sem_trywait((sem_t*)&m_sem) == 0);
        else
            return (sem_wait ((sem_t*)&m_sem) == 0);
    #endif
    }

    // 等待指定的毫秒数,直到信号值大于0,然后将其减1返回真.如果在所指定的时间内信号灯值一直小于等于0,则返回假.
    //   npMillseconds:  所等待的毫秒数,为0表示不等待.
#if defined (_PF_WINDOWS)
    inline_ BOOL_P wait_timeout (const INT_P npMillseconds) const
    {
        ASSERT (npMillseconds >= 0);
        return (::WaitForSingleObject (m_hSemaphore, (DWORD)npMillseconds) == WAIT_OBJECT_0);
    }
#elif defined (_PF_LINUX)
    BOOL_P wait_timeout (const INT_P npMillseconds) const;
#endif

    // 信号灯值加1,从而允许一个正在wait方法处等待的线程成功通过.
    inline_ void post () const
    {
    #if defined (_PF_WINDOWS)
        ::ReleaseSemaphore (m_hSemaphore, 1, 0);
    #elif defined (_PF_LINUX)
        sem_post ((sem_t*)&m_sem);
    #endif
    }

    // 将信号灯值重置为零
    inline_ void reset ()
    {
        while (wait (TRUE));
        ASSERT (GetValue () == 0);
    }

#if defined (_PF_WINDOWS)
    inline_ HANDLE GetHandle () const
    {
        return m_hSemaphore;
    }
#endif

    // 返回信号灯的当前值
    // 注意: 执行本方法时,本信号灯对象必须还未在多线程中使用,否则本方法返回值不见得就是信号灯的当前实际值.
    inline_ INT_P GetValue () const
    {
    #if defined (_PF_WINDOWS)
        INT_P npValue = 0;
        while (wait (TRUE))
            npValue++;
        for (INT_P i = 0; i < npValue; i++)
            post ();
        return npValue;
    #elif defined (_PF_LINUX)
        INT nValue = -1;
        VERIFY_EQUAL (sem_getvalue ((sem_t*)&m_sem, &nValue), 0);
        return nValue;
    #endif
    }

private:
#if defined (_PF_WINDOWS)
    mutable HANDLE m_hSemaphore;
#elif defined (_PF_LINUX)
    sem_t m_sem;
#endif
};

//-----------------------------------------------------------------------

// 读写锁
class CMReadWriteLock : public CVolCommonBase
{
public:
    inline_ CMReadWriteLock ()
    {
        m_npNumReaders = 0;
    }

public:
    inline_ void LockRead () const
    {
        CMutexLocker locker (m_mxRead);
        ASSERT (m_npNumReaders >= 0);

        m_npNumReaders++;
        if (m_npNumReaders == 1)
            m_mxWrite.lock ();  // 锁住写操作,当有读操作时只锁一次.
    }

    inline_ void UnLockRead () const
    {
        CMutexLocker locker (m_mxRead);
        ASSERT (m_npNumReaders >= 0);

        m_npNumReaders--;
        if (m_npNumReaders == 0)
            m_mxWrite.unlock ();  // 允许写操作
    }

    inline_ void LockWrite () const
    {
        m_mxWrite.lock ();
    }

    inline_ void UnLockWrite () const
    {
        m_mxWrite.unlock ();
    }

protected:
    mutable INT_P m_npNumReaders;
    CMMutex m_mxRead, m_mxWrite;
};

//-----------------------------------------------------------------------

#if defined (_PF_WINDOWS)

class CSyncEvent : public CVolCommonBase  // 事件
{
public:
    inline_ CSyncEvent (const TCHAR* szEventName = NULL)
    {
        ASSERT_R_STR_OR_NULL (szEventName);
        m_hEvent = ::CreateEvent (NULL, FALSE, FALSE, szEventName);
    }

    inline_ ~CSyncEvent ()
    {
        ::CloseHandle (m_hEvent);
    }

    // 如果blpTry为真,则只测试下,如果事件被置位,则将其复位后(手动复位为假)立即成功返回真,否则立即返回假.
    // 如果blpTry为假,则无限等待直到事件被置位,然后将其复位后(手动复位为假)返回真.
    inline_ BOOL_P wait (const BOOL_P blpTry = FALSE) const
    {
        return (::WaitForSingleObject (m_hEvent, (blpTry ? 0 : INFINITE)) == WAIT_OBJECT_0);
    }

    inline_ BOOL_P wait_timeout (const INT_P npMillseconds) const
    {
        ASSERT (npMillseconds >= 0);
        return (::WaitForSingleObject (m_hEvent, (DWORD)npMillseconds) == WAIT_OBJECT_0);
    }

    // 去除事件的置位
    inline_ void reset () const
    {
        ResetEvent (m_hEvent);
    }

    // 将事件置位,从而允许一个等待线程通过,线程通过后自动去除事件的置位.
    inline_ void post () const
    {
        /*  此处的差异即为无法利用pthread_cond_xxx条件变量来构建linux下的本类实现的原因:
        pthread_cond_signal:  The pthread_cond_broadcast() and pthread_cond_signal() functions shall
            have no effect if there are no threads currently blocked on cond.
        SetEvent:  The state of an auto-reset event object remains signaled until a single waiting thread
            is released, at which time the system automatically sets the state to nonsignaled. If no threads
            are waiting, the event object's state remains signaled. */
        SetEvent (m_hEvent);
    }

    inline_ HANDLE GetHandle () const
    {
        return m_hEvent;
    }

private:
    mutable HANDLE m_hEvent;
};

#endif

//-----------------------------------------------------------------------

#define _WAITTING_EVENT_HANDLE_ARRAY(ary)  (DWORD)NUM_ELEMENTS_OF (ary), (const HANDLE*)(ary)

BOOL_P VolBeginThread (LPTHREAD_START_ROUTINE fnThread, const INT_P npUserParam,
        const INT_P npStackSize, const INT_P npPriority, const BOOL_P blpWaitThreadExit);

class CVolThreadState : public CVolCommonBase
{
public:
    CVolThreadState ();
    ~CVolThreadState ();

public:
    void Reset ();

    inline_ void OnThreadExit ()
    {
        ::SetEvent (m_hEventExited);
    }
    inline_ BOOL_P IsRunning () const
    {
        return (WaitForSingleObject (m_hEventExited, 0) == WAIT_TIMEOUT);  // != WAIT_OBJECT_0
    }

    void SetUserVolObjectPtr (const INT_P npIndex, const CVolObject* pObject);
    
    inline_ void SetUserVolObject (const INT_P npIndex, const CVolObject& obj)
    {
        SetUserVolObjectPtr (npIndex, (obj.IsNullObject () ? NULL : &obj));
    }

    BOOL_P GetUserVolObject (const INT_P npIndex, CVolObject& obj) const;

    inline_ BOOL_P IsNeedExit (const INT_P npMilliseconds)
    {
        return (WaitForSingleObject (m_hEventNeedExit, (DWORD)npMilliseconds) != WAIT_TIMEOUT);  // == WAIT_OBJECT_0
    }
    inline_ BOOL_P WaitThreadExit (const INT_P npMilliseconds)
    {
        VERIFY (SetEvent (m_hEventNeedExit));
        return (WaitForSingleObject (m_hEventExited, (DWORD)npMilliseconds) != WAIT_TIMEOUT);  // == WAIT_OBJECT_0
    }

private:
    HANDLE m_hEventNeedExit, m_hEventExited;

    CMMutex m_lockerUserVolObject;
    CVolObject* m_apUserVolObjects [2];

public:
    volatile INT_P m_npUserData;
};

//-----------------------------------------------------------------------

//   在线程函数循环中,如果发现*pblpExit(pblpExit必定不为NULL)为真,则应该尽快退出返回.
//   在windows操作系统中另外提供了一个等价退出信号hExitEventOnWindows(事件对象句柄),
// 如果该事件被置位,也应该尽快退出返回.这两个退出信号要么同时被设置要么同时未被设置,
// 所以在windows操作系统中可以任选一个条件进行检查.
typedef void (*VOL_THREAD_FUNC) (void* param, volatile const BOOL_P* pblpExit, HANDLE hExitEventOnWindows);

//   线程封装类
//   多线程编程注意事项: 任何直接或间接使用了多线程的类,在其类对象析构/清理函数中都必须首先
// 退出线程,避免产生多线程冲突.
class CVolThread : public CVolCommonBase
{
public:
    inline_ CVolThread ()
    {
    #if defined (_PF_WINDOWS)
        m_handle = NULL;
        m_idThread = 0;
    #endif
        m_blpExit = FALSE;
        m_blpRunning = FALSE;
    }

    inline_ ~CVolThread ()
    {
        Exit ();
    }

    // 启动线程. 注意: 本方法只能在主线程中调用
    // fnThreadMain指定线程主函数,如果为NULL,则表明启动本对象的main方法.
    // param提供线程启动参数
    // npStackSize指定线程堆栈尺寸(以字节为单位),为0表示使用默认值.
    BOOL_P Start (const VOL_THREAD_FUNC fnThreadMain = NULL, void* param = NULL, const INT_P npStackSize = 0);

    // 通知并等待线程退出. 注意: 本方法只能在主线程中调用
    void Exit ();

    // 通知线程退出但不等待其退出. 注意: 本方法只能在主线程中调用
    void PostExitNotify ();

    // 通知并等待线程退出. 注意: 本方法只能在主线程中调用
    // 本方法适用于线程基于semWork信号灯启动实际工作的机制,譬如线程主体循环类似以下形式:
    // while (m_blpExit == FALSE)
    // {
    //     semWork.wait_timeout (nWaitingMillseconds);
    //     // working...
    // }
    inline_ void Exit (CMSemaphore& semWork)
    {
        // 设置线程处于等待退出状态,必须在下面的semWork信号置位前设置,以免线程在识别到退出状态前重新进入了工作信号灯等待状态.
        m_blpExit = TRUE;  // 设置线程处于等待退出状态
        semWork.post ();  // 置位所指定的工作信号灯,以退出工作等待状态.
        Exit ();  // 通知并等待线程退出
    }

    // 用作在所启动线程中执行,一旦发现此方法返回真,就需要尽快退出线程的执行.
    //   npMillseconds: 等待线程退出通知的最大时间,单位毫秒. 为0表示不等待,为-1表示一直等待.
    BOOL_P IsNeedExit (INT_P npMillseconds) const;

#if defined (_PF_WINDOWS)
    inline_ HANDLE GetHandle () const
    {
        return m_handle;
    }

    inline_ DWORD GetThreadID () const
    {
        return m_idThread;
    }
#endif

    // 返回线程是否正在运行中
    inline_ BOOL_P IsRunning () const
    {
        return m_blpRunning;
    }

protected:
#if defined (_PF_WINDOWS)
    static DWORD WINAPI sThreadCallOther (CVolThread* pThread);
    static DWORD WINAPI sThreadCallSelf (CVolThread* pThread);
#elif defined (_PF_LINUX)
    static void* sThreadCallOther (CVolThread* pThread);
    static void* sThreadCallSelf (CVolThread* pThread);
#endif

    //   当调用Start方法时如果fnThreadMain参数为NULL,则此为线程的主函数.
    //   此线程函数循环中,如果发现m_evExit置位(windows)或者m_blpExit为真(两个条件
    // 要么同时满足要么同时不满足,所以可以任选一个条件进行检查),则应该尽快退出返回.
    virtual void main (void* param)
    {
    }

    // 当所启动线程执行完毕后,本方法被调用.
    // 注意本方法在多线程中被调用.
    virtual void thOnThreadRunOver ()
    {
    }

protected:
#if defined (_PF_WINDOWS)
    HANDLE m_handle;
    DWORD m_idThread;
    CSyncEvent m_evExit;  // 线程退出事件(方便使用winapi同时等待多个信号量)
#endif
    volatile BOOL_P m_blpExit;  // 线程退出信号逻辑值
    volatile BOOL_P m_blpRunning;  // 记录线程是否正在运行

    // 临时成员:
    VOL_THREAD_FUNC m_fnThreadMain;  // 线程主函数,如果为NULL,则表明启动本对象的main方法.
    void* m_pmThread;  // 线程运行参数
};

//-----------------------------------------------------------------------

#if defined (_PF_WINDOWS)

typedef UINT_P HVOLTHREAD;

class CVolPoolThreadInfo : public CVolCommonBase
{
public:
    inline_ CVolPoolThreadInfo ()
    {
        init ();
    }

    inline_ void init ()
    {
        m_hThreadHandle = 0;
        m_pOwnerObject = NULL;
    }

    inline_ void init (HVOLTHREAD hThreadHandle, CVolObject* pOwnerObject)
    {
        m_hThreadHandle = hThreadHandle;
        m_pOwnerObject = pOwnerObject;
    }

    HVOLTHREAD m_hThreadHandle;
    CVolObject* m_pOwnerObject;
};

// 用户线程函数格式,
// 注意:
//   1. 在用户线程函数中,如果发现hBreakEvent信号被置位,应该尽快退出返回;
//   2. 在用户线程函数中不允许对窗口界面直接进行操作,否则可能导致死锁.
typedef void (CALLBACK *VOL_POOL_THREAD_FUNC) (HVOLTHREAD hVolThread, UINT_P upParam1, UINT_P upParam2, HANDLE hBreakEvent);

// 支持线程池的线程
class CVolPoolThread : public CVolCommonBase
{
public:
    CVolPoolThread ();

    virtual ~CVolPoolThread ()
    {
        Exit ();
    }

    virtual void Destroy ()
    {
        delete this;
    }

public:  // 这些方法只能由CVolThreadPool类调用
    BOOL_P Start (VOL_POOL_THREAD_FUNC fnThreadMain, UINT_P upParam1, UINT_P upParam2, HVOLTHREAD hAllocedVolThread);
    void Exit ();  // 通知并等待线程退出

    // 通知用户线程函数退出执行以将线程返回到空闲状态.
    void BreakToIdle ();

    BOOL_P IsIdle (UINT_P* pupIdleBeginTime) const;  // 返回当前是否处于空闲状态及进入空闲状态的时间
    BOOL_P IsRunning () const;
    BOOL_P SafeIsNeedBreak () const;

    inline_ HANDLE GetBreakEventHandle () const
    {
        return m_evBreak.GetHandle ();
    }

    inline_ INT_P GetState () const
    {
        CMutexLocker locker (m_mxThread);
        return m_npState;
    }

    inline_ HVOLTHREAD GetHandle () const
    {
        CMutexLocker locker (m_mxThread);
        return m_hVolThread;
    }

protected:
    DWORD main ();
    void ResetAllEvents ();
    static DWORD WINAPI sThreadMain (LPVOID lpThreadParameter);

protected:
    HVOLTHREAD m_hVolThread;  // 所对应的火山线程句柄

    CSyncEvent m_evBreak;  // 用作通知用户线程函数退出
    CSyncEvent m_evIdle;  // 线程空闲时等待重启事件
    CSyncEvent m_evContinue;  // 线程等待继续事件
    CMMutex m_mxThread;  // 操作锁

    BOOL_P m_blpExitThread;  // 用作通知线程完全退出(不再需要进入空闲状态)
    BOOL_P m_blpBreak;  // 用作通知用户线程函数退出
    UINT_P m_upIdleBeginTime;  // 当前线程进入空闲状态的时间(单位毫秒),0表示尚未进入空闲状态.
    volatile INT_P m_npState;  // 当前运行状态,为"VPTS_"宏值之一.

    VOL_POOL_THREAD_FUNC m_fnThreadMain;  // 线程主函数
    UINT_P m_upParam1, m_upParam2;  // 线程运行参数
};

typedef CMPointerArray<CVolPoolThread*> CVolPoolThreadArray;

// 线程池. 注意本类中的方法除了IsThreadNeedBreak均只能在主线程中执行.
class CVolThreadPool : public CVolCommonBase
{
public:
    // npPoolUpdateInterval: 当调用 UpdatePool (FALSE) 时的更新时间间隔. 单位毫秒.
    CVolThreadPool (const INT_P npPoolUpdateInterval = 1000);

    inline_ ~CVolThreadPool ()
    {
        Cleanup ();
    }

public:
    // 清理本对象的内容,退出所有正在执行的线程.
    void Cleanup ();

    // 设置最多能同时保留的空闲线程数目
    //   npMaxNumIdleThreads: 最多能同时保留的空闲线程数目,为0表示使用默认值.
    void SetMaxNumIdleThreads (const INT_P npMaxNumIdleThreads = 0);

    // 设置线程最大允许空闲时间(单位毫秒)
    //   npMaxThreadIdleInterval: 线程最大允许空闲时间(单位毫秒),为0表示使用默认值.
    void SetMaxThreadIdleInterval (const INT_P npMaxThreadIdleInterval = 0);

    // 更新线程池,可以在系统空闲时手动调用本方法进行更新. 主要做以下工作:
    //   1. 检查删除线程池中所有超出最大空闲时间的线程;
    //   2. 检查删除线程池中所保留的过多数目空闲线程.
    // 本方法调用不是必需的,在调用其它本类方法时会自动调用本方法.
    //   blpUpdateAtOnce: 为真则立即更新,为假则首先检查距上次更新是否超过了所指定时间,如已经超过则更新,未超过则不更新.
    //      在系统空闲时手动调用本方法时可以提供为假,以避免过于频繁地操作.
    void UpdatePool (const BOOL_P blpUpdateAtOnce);

    // 创建并启动一个新线程,该线程会优先从线程池中提取使用. 返回其句柄,失败返回NULL.
    //   fnThreadMain: 用户线程函数地址,不能为NULL.
    //   upParam1, upParam2: 提供到用户线程函数的参数值
    // 注意:
    //   1. 所返回句柄在用户线程函数执行完毕后,该线程将会被自动释放进线程池中,此时所返回句柄值将自动永久失效;
    //   2. 如果所提供用户线程函数一直在执行,可以调用"StopThread"方法通知用户线程函数停止执行并释放该线程.
    HVOLTHREAD StartNewThread (VOL_POOL_THREAD_FUNC fnThreadMain, UINT_P upParam1 = 0, UINT_P upParam2 = 0);

    // 等待所指定线程执行完毕,然后将该线程释放进线程池.
    // 如果hVolThread句柄值为0或已经失效,将直接返回不进行任何处理.
    void StopThread (HVOLTHREAD hVolThread);

    // 用作在所启动线程的用户线程函数中执行,一旦发现此方法返回真,用户线程函数就需要尽快退出.
    //   npMillseconds: 等待退出通知的最大时间,单位毫秒. 为0表示不等待,为-1表示一直等待.
    // 如果hVolThread句柄值已经失效,将始终返回真.
    BOOL_P IsThreadNeedBreak (HVOLTHREAD hVolThread, INT_P npMillseconds) const;

    // 返回所指定线程是否正在运行
    BOOL_P IsThreadRunning (HVOLTHREAD hVolThread) const;

    // 调试时返回本线程池的描述文本
    CVolString& DebugGetDumpString (CVolString& strDump);

protected:
    CVolPoolThread* _FindThread (HVOLTHREAD hVolThread) const;
    HVOLTHREAD _AllocThreadHandle ();

protected:
    CMMutex m_mxPool;  // 操作锁
    const INT_P m_npPoolUpdateInterval;  // 当调用 UpdatePool (FALSE) 时的更新时间间隔. 单位毫秒.

    INT_P m_npMaxNumIdleThreads;  // 最多能同时保留的空闲线程数目,必定大于0.
    INT_P m_npMaxThreadIdleInterval;  // 线程的最大允许空闲时间(单位毫秒),必定大于0.
    UINT_P m_upFreeThreadID;  // 当前可用线程句柄ID
    UINT_P m_upLastUpdateTime;  // 最近一次更新时间,为0表示尚未更新过.

    CVolPoolThreadArray m_arypThreads;  // 当前所有创建的线程
};

// 简单完成端口实现类
class CSimpleCompletionPort : public CVolCommonBase
{
public:
    inline_ CSimpleCompletionPort ()
    {
        m_hCompletionPort = NULL;
    }

    inline_ ~CSimpleCompletionPort ()
    {
        Cleanup ();
    }

public:
    inline_ BOOL_P Create (INT_P npFileHandle, INT_P npExistingCompletionPort, INT_P npCompletionKey)
    {
        Cleanup ();
        m_hCompletionPort = ::CreateIoCompletionPort ((HANDLE)npFileHandle, (HANDLE)npExistingCompletionPort, (ULONG_PTR)npCompletionKey, 0);
        return (m_hCompletionPort != NULL);
    }

    inline_ void Cleanup ()
    {
        if (m_hCompletionPort != NULL)
        {
            VERIFY (::CloseHandle (m_hCompletionPort));
            m_hCompletionPort = NULL;
        }
    }

    inline_ INT_P GetHandle () const
    {
        return (INT_P)m_hCompletionPort;
    }

    BOOL_P wait (INT_P* pnpParam1, INT_P* pnpParam2, INT* pnParam3, INT nMilliseconds);

    inline_ BOOL_P post (INT_P npParam1, INT_P npParam2, INT nParam3)
    {
        return (m_hCompletionPort != NULL && ::PostQueuedCompletionStatus (
                m_hCompletionPort, (DWORD)nParam3, (ULONG_PTR)npParam1, (LPOVERLAPPED)npParam2));
    }

protected:
    HANDLE m_hCompletionPort;
};

#endif

#endif
