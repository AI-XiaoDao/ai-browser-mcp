
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_CLASSES_H__
#define __VOL_CLASSES_H__

class CVolObject;
class CVolBaseInputStream;
class CVolBaseOutputStream;

//--------------------------------------------------------------------------------------

// 用作记录一个火山对象指针
class CVolObjectPointer : public CRefObject
{
public:
    inline_ CVolObjectPointer (CVolObject* pVolObject)
    {
        ASSERT (pVolObject != NULL);
        m_pVolObject = pVolObject;
    }

    // 释放对象参考并设置清除对象指针记录
    inline_ void ReleasePointer ()
    {
        m_pVolObject = NULL;
        Release ();
    }

    inline_ CVolObject* GetVolObject () const
    {
        return m_pVolObject;
    }

    inline_ CVolObject* SafeGetVolObject () const
    {
        return (this == NULL ? NULL : m_pVolObject);
    }

protected:
    CVolObject* m_pVolObject;  // 用作记录对应的火山对象指针
};

//--------------------------------------------------------------------------------------

// 用作记录一个火山事件接收对象指针
class _NAME_COMPILER_AGREED (CVolEventObjectPointer) : public CRefObject
{
public:
    inline_ CVolEventObjectPointer (CVolObject* pVolObject)
    {
        ASSERT (pVolObject != NULL);
        m_npNumSendingEvents = 0;
        m_pVolObject = pVolObject;
    }

public:
    // 释放对象参考并设置清除对象指针记录
    inline_ void _NAME_COMPILER_AGREED (ReleasePointer) ()
    {
        m_mxEventSend.lock ();  // m_mxEventSend不需要解锁,以彻底阻断事件发送.

        m_pVolObject = NULL;
        Release ();  // 释放对象参考
    }

    inline_ CVolObject* _NAME_COMPILER_AGREED (GetVolObject) ()
    {
        ASSERT (m_pVolObject != NULL);
        return m_pVolObject;
    }

private:
    friend class CVolEventReceiver;

    BOOL_P BeginSendEvent ();
    void EndSendEvent ();

protected:
    mutable INT_P m_npNumSendingEvents;
    CMMutex m_mxCounter, m_mxEventSend;

    CVolObject* m_pVolObject;  // 用作记录对应的火山对象指针
};

// 火山事件接收器
class _NAME_COMPILER_AGREED (CVolEventReceiver) : public CVolCommonBase
{
public:
    CVolEventReceiver ();

    inline_ ~CVolEventReceiver ()
    {
        if (m_pEventReceiver != NULL)
            m_pEventReceiver->Release ();
    }

public:
    // 置入事件接收者
    //   fnReceiver: 事件接收函数指针,为NULL表示删除已经置入的事件接收器.
    //   pEventReceiver: 事件接收对象,fnReceiver不为NULL时不能为NULL.
    //   nTagNumber: 事件标签值
    void _NAME_COMPILER_AGREED (SetReceiver) (VOID_FUNC fnReceiver, CVolEventObjectPointer* pEventReceiver, INT nTagNumber);

    // 准备开始发送事件,成功返回非NULL火山事件对象指针(此时其GetVolObject必定返回非NULL值),失败返回NULL.
    //   pfnReceiver: 不能为NULL,用作返回对应的事件接收函数指针. 仅当本方法返回真值时被填写.
    //   pnTagNumber: 不能为NULL,用作返回对应的标记值. 仅当本方法返回真值时被填写.
    CVolEventObjectPointer* _NAME_COMPILER_AGREED (BeginSendEvent) (VOID_FUNC* pfnReceiver, INT* pnTagNumber);

    // 结束发送事件. 当BeginSendEvent执行返回非NULL值后必须对应调用本方法结束.
    //   pEventReceiver: BeginSendEvent的返回值
    static void _NAME_COMPILER_AGREED (sEndSendEvent) (CVolEventObjectPointer* pEventReceiver);

protected:
    CVolSpinLock m_locker;

    VOID_FUNC m_fnReceiver;  // 事件接收函数指针,未被设置则为NULL.
    CVolEventObjectPointer* m_pEventReceiver;  // 事件接收对象,m_fnReceiver不为NULL时必定不为NULL.
    INT m_nTagNumber;  // 事件标签值
};

//--------------------------------------------------------------------------------------

#define VE_NONE  0  // 无异常
#define VE_INIT_EXTERN_FUNC_TABLE_FAILED  -1  // 初始化外部函数表失败

// 系统基本异常类
class CVolException : public CVolObject
{
    DECLARE_GLOBAL_VOL_CLASS (CVolException)

public:
    inline_ CVolException ()
    {
        m_nCode = 0;
    }

    inline_ CVolException (const INT nCode, const TCHAR* szDesc)
    {
        m_nCode = nCode;
        m_strDesc.SetText (szDesc);
    }

public:
    virtual void GetDumpString (CVolString& strDump, INT nMaxDumpSize) override
    {
        strDump.AddFormatText (_T_VOL_EXCEPTION_DUMP_DS, m_nCode, m_strDesc.GetText ());
    }

    virtual void LoadFromStream (CVolBaseInputStream& stream) override
    {
        stream >> m_nCode >> m_strDesc;
    }

    virtual void SaveIntoStream (CVolBaseOutputStream& stream) override
    {
        stream << m_nCode << m_strDesc;
    }

public:
    INT m_nCode;  // 异常代码: 0表示无; 小于0: 系统内部使用的异常代码; 大于0: 用户使用的异常代码
    CVolString m_strDesc;  // 异常描述
};

//--------------------------------------------------------------------------------------

// 所有基本数据类型的基础封装类
class _NAME_COMPILER_AGREED (CVolBaseDataType) : public CVolObject
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolBaseDataType)

public:
    inline_ CVolBaseDataType ()
    {
    }

    // 用作返回对应的基本数据指针
    virtual void* GetDataPtr ()
    {
        return NULL;
    }
};

//--------------------------------------------------------------------------------------

// 用户程序类的基础类
class _NAME_COMPILER_AGREED (CVolUserApp) : public CVolObject
{
    DECLARE_GLOBAL_EMPTY_VOL_CLASS (CVolUserApp)

public:
    CVolUserApp ();

    //   返回来自用户程序的某些特定类的运行时信息列表,该列表中的成员数目为
    // _NUM_SPEC_USER_CLASS_TYPES,对应从0开始的各个枚举类型.
    typedef enum
    {
        SUCT_UNKNOWN = -1,

        // 各种基本数据类型的封装类:
        SUCT_PKG_SBYTE = 0,  // 字节类
        SUCT_PKG_SHORT,      // 短整数类
        SUCT_PKG_WCHAR,      // 字符类
        SUCT_PKG_INT,        // 整数类
        SUCT_PKG_VINT,       // 变整数类
        SUCT_PKG_LONG,       // 长整数类
        SUCT_PKG_FLOAT,      // 单精度小数类
        SUCT_PKG_DOUBLE,     // 小数类
        SUCT_PKG_BOOL,       // 逻辑型类

        _NUM_SPEC_USER_CLASS_TYPES
    }
    SPEC_USER_CLASS_TYPE;
    virtual const CVolRuntimeClass** GetSpecialUserRuntimeClasses () const
    {
        return NULL;
    }

    // 查找指定对象所对应的用户程序特定类
    SPEC_USER_CLASS_TYPE FindSpecialUserClassType (const CVolObject* pVolObject) const;
};

//--------------------------------------------------------------------------------------

// 本接口类用作通过窗口消息的方式把程序自定义消息发送到主UI线程处理
class IVolNoticeReceiver
{
public:
    inline_ IVolNoticeReceiver ()
    {
        m_hWnd = NULL;
        InitReceiver ();
    }

    ~IVolNoticeReceiver ();

public:
    // 用作发送程序自定义消息到主UI线程中处理,直到该消息处理完毕后本方法才会返回.
    // 返回该消息是否已经被成功发送到本类的OnNotify处理方法.
    // 本方法可以在多线程环境中执行.
    //   npCode: 自定义消息代码值
    //   npParam1, npParam2: 消息参数
    //   pnpResult: 如果不为NULL,则在其中置入OnNotify方法的返回值(即使本方法返回失败,此指针值也会被置为0).
    BOOL_P Notify (INT_P npCode, INT_P npParam1, INT_P npParam2, INT_P* pnpResult);

    // 投递通知
    void Post (INT_P npCode, INT_P npParam1);

protected:
    // 用作在继承类中覆盖接收并处理通知,返回处理结果值.
    //   npCode: 自定义消息代码值
    //   npParam1, npParam2: 消息参数
    virtual INT_P OnNotify (INT_P npCode, INT_P npParam1, INT_P npParam2)
    {
        return 0;
    }
    
private:
    static LRESULT CALLBACK sVolNoticeRevWindowProc (HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);
    BOOL_P InitReceiver ();  // 初始化本对象,返回是否成功. 本对象必须处于初始状态.

protected:
    HWND m_hWnd;
};

//--------------------------------------------------------------------------------------

// 本类支持Post携带对象参数
class IVolAdvNoticeReceiver
{
public:
    IVolAdvNoticeReceiver ();
    ~IVolAdvNoticeReceiver ();

public:
    // 用作发送程序自定义消息到主UI线程中处理,直到该消息处理完毕后本方法才会返回.
    // 返回该消息是否已经被成功发送到本类的OnNotify处理方法.
    // 本方法可以在多线程环境中执行.
    //   npCode: 自定义消息代码值
    //   npParam1, npParam2, pParamObject: 消息参数
    //   pnpResult: 如果不为NULL,则在其中置入OnNotify方法的返回值(即使本方法返回失败,此指针所指向值也会被置为0).
    BOOL_P SendNotice (INT_P npCode, INT_P npParam1, INT_P npParam2, CRefObject* pParamObject, INT_P* pnpResult);

    // 投递通知,本方法立即返回并不会等待通知处理完毕.
    // 注意: 被投递通知如果超过所指定时间(SetMaxPostedNoticeKeepTime指定)未投递成功,将被取消.
    void PostNotice (INT_P npCode, INT_P npParam1, INT_P npParam2, CRefObject* pParamObject);

    //   设置被投递(调用PostNotice方法)通知的最大保留时间(单位毫秒),超过最大保留时间
    // 尚未投递成功的通知将被自动删除,为0表示永远保留直到投递成功.
    void SetMaxPostedNoticeKeepTime (INT nMaxPostedNoticeKeepTime);
    inline_ INT GetMaxPostedNoticeKeepTime () const
    {
        return (INT)m_dwMaxPostedNoticeKeepTime;
    }

protected:
    // 用作在继承类中覆盖接收并处理通知,返回处理结果值.
    //   npCode: 自定义消息代码值
    //   npParam1, npParam2, pParamObject: 消息参数
    virtual INT_P OnNotify (INT_P npCode, INT_P npParam1, INT_P npParam2, CRefObject* pParamObject)
    {
        return 0;
    }
    
private:
    static LRESULT CALLBACK sVolAdvNoticeRevWindowProc (HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam);
    BOOL_P InitReceiver ();  // 初始化本对象,返回是否成功. 本对象必须处于初始状态.
    void ProcessPostedNotice (const UINT_P upNoticeNumber);
    void CheckFreeTimeoutNotices ();

protected:
    HWND m_hWnd;
    UINT_P m_upFreeNoticeNumber;  // 当前可用的消息编号(投递方法使用)
    DWORD m_dwMaxPostedNoticeKeepTime;  // 见SetMaxPostedNoticeKeepTime

    CMMutex m_mxLocker;
    CVolMem m_memPostedNotices;  // _VOL_ADV_POSTED_NOTICE数组,用作记录所有调用PostNotice方法投递且尚未投递成功的通知.
};

//--------------------------------------------------------------------------------------

class CWindowTimeTrigger : public CVolCommonBase
{
public:
    inline_ CWindowTimeTrigger (const DWORD dwTriggerInterval = 0)
    {
        Reset (dwTriggerInterval);
    }

public:
    // 重置并启动本触发器
    //   dwTriggerInterval:  触发周期时间,单位毫秒.等于0表示触发器被停止.
    void Reset (const DWORD dwTriggerInterval);

    // 返回当前触发周期时间.单位毫秒.等于0表示触发器被停止.
    inline_ DWORD GetTriggerInterval () const
    {
        return m_dwTriggerInterval;
    }

    // 停止本触发器. 启动需要重新调用Reset.
    inline_ void Stop ()
    {
        m_dwTriggerInterval = m_dwNextTriggerTime = 0;
    }

    // 用户需要周期性调用本方法通知时钟已经前进一段时间
    // 如果本触发器此时被触发(刚重置后会固定触发一次),返回真,否则返回假.
    BOOL_P OnTimeAdvance ();

    // 手动更改下一次的触发周期.
    // 注意: 本次更改只影响下一次的触发,下一次触发后将回归正常的触发周期.
    void SetNextTriggerInterval (const DWORD dwNextTriggerInterval);

protected:
    DWORD m_dwTriggerInterval;  // 触发周期时间,单位毫秒.等于0表示触发器被停止.
    DWORD m_dwNextTriggerTime;  // 下一次触发时间
};

//--------------------------------------------------------------------------------------

// 火山部件DLL的输出函数原型
typedef void (CALLBACK *VOL_COM_DLL_FUNC) ();  // _NAME_COMPILER_AGREED

// 用作记录火山类的签名信息
typedef struct
{
    UINT_P m_upClassSize;  // 类的数据尺寸,为0表示为签名信息表的结束项.
}
_NAME_COMPILER_AGREED (VOL_CLASS_SIGNATURE_INFO);

// 用作记录火山类的签名信息(包括类的全名)
typedef struct
{
    const TCHAR* m_szClassFullName;  // 类的全名
    VOL_CLASS_SIGNATURE_INFO m_infSign;
}
_NAME_COMPILER_AGREED (VOL_CLASS_SIGNATURE_INFO_WITH_NAME);

// 获取火山部件DLL信息,返回其接口函数表.
//   ppVolSysClassSignInfo: 用作返回火山部件DLL接口程序中所使用相关系统类的签名信息表,以m_upClassSize为0的类数据尺寸成员标志结束. 本参数不能提供NULL,其中返回NULL表示无类签名信息表.
#define _AT_VOL_COM_INFO_GETTER_NAME  "get_vol_com_dll_info"  // 获取火山部件DLL信息的接口函数名 _NAME_COMPILER_AGREED
typedef VOL_COM_DLL_FUNC* (CALLBACK *FN_GET_VOL_COM_INFO) (const VOL_CLASS_SIGNATURE_INFO** ppVolSysClassSignInfo);

// 火山部件DLL载入器
class _NAME_COMPILER_AGREED (CVolComDllLoader) : public CVolCommonBase
{
public:
    // szDllFileName: 提供火山部件DLL的文件名,必须是常量文本.
    // pVolSysClassSignInfo: 提供火山部件DLL接口程序中所使用相关系统类的签名信息表,以m_upClassSize为0的类数据尺寸成员标志结束,为NULL表示无. 必须为常量数据.
    CVolComDllLoader (const TCHAR* szDllFileName, const VOL_CLASS_SIGNATURE_INFO_WITH_NAME* pVolSysClassSignInfo);
    inline_ ~CVolComDllLoader ()
    {
        Cleanup ();
    }

    VOL_COM_DLL_FUNC _NAME_COMPILER_AGREED (GetFunc) (const INT_P npFuncIndex);
    void Cleanup ();

protected:
    virtual INT_P CheckSysClassSignInfo (const VOL_CLASS_SIGNATURE_INFO* pVolSysClassSignInfo1,
            const VOL_CLASS_SIGNATURE_INFO_WITH_NAME* pVolSysClassSignInfo2, CMVoidPtrArray& aryNotMatchSysClassSignInfos) const;

protected:
    const TCHAR* const m_szDllFileName;
    const VOL_CLASS_SIGNATURE_INFO_WITH_NAME* const m_pVolSysClassSignInfo;

    H_LIB m_hLib;
    VOL_COM_DLL_FUNC* m_pFuncTable;
    CMMutex m_mxGetFunc;
};

// _NAME_COMPILER_AGREED
#define _BASE_VOL_COM_INTERFACE_CODE  \
        CVolObjectDestroyer m_objVolComInsideDll;  \
        inline_ CVolObject* GetVolComObject () const { return m_objVolComInsideDll.GetVolObject (); }  \
        inline_ void DiscardVolComObject () { m_objVolComInsideDll.Discard (); }  \
        virtual void GetDumpString (CVolString& strDump, INT nMaxDumpSize) override { GetVolComObject ()->GetDumpString (strDump, nMaxDumpSize); }  \
        virtual void LoadFromStream (CVolBaseInputStream& stream) override { GetVolComObject ()->LoadFromStream (stream); }  \
        virtual void SaveIntoStream (CVolBaseOutputStream& stream) override { GetVolComObject ()->SaveIntoStream (stream); }

#endif
