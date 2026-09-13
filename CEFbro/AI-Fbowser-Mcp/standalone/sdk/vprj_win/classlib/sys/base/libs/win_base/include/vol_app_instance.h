
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_APP_INSTANCE_H__
#define __VOL_APP_INSTANCE_H__

// 火山图片资源的类型
typedef enum
{
    VRIT_BITMAP = 0,  // 位图
    VRIT_CURSOR,      // 光标
    VRIT_ICON,        // 图标
    VRIT_IMAGE_LIST,  // 图片组

    _NUM_VOL_RES_IMAGE_TYPES
}
VOL_RES_IMAGE_TYPE;

// 用作在图片组位图中填充其中透明色部分的颜色值
#define VIL_TRANSPARENT_COLOR  RGB (255, 0, 255)

//-----------------------------------------------------------------------------------------------

typedef struct
{
    const TCHAR* m_szLibFileName;  // 所处外部库文件名,为空文本表示与上一项相同,为NULL表示表项的结束.
    const U8CHAR* m_szFuncName;  // 输出函数名
    VOID_FUNC _NAME_COMPILER_AGREED (m_func);  // 用作记录所获取到的函数指针
}
_NAME_COMPILER_AGREED (EXTERN_FUNC_ITEM);

// 外部函数表载入器
class CExternFunctionLoader : public CVolCommonBase
{
public:
    inline_ CExternFunctionLoader ()
    {
    }

    inline_ ~CExternFunctionLoader ()
    {
        Cleanup ();
    }

    void Cleanup ();

public:
    // 初始化外部函数表,返回是否成功.
    //   pExternFuincTable: 提供待初始化的外部函数表
    //   blpThrowExceptionIfFailed: 如果初始化失败是否抛出 VE_INIT_EXTERN_FUNC_TABLE_FAILED 异常.
    // 如果构造本对象时blpFailExit参数为真,则失败时会直接报错退出应用程序而不会返回NULL.
    BOOL_P InitExternFuncTable (EXTERN_FUNC_ITEM* pExternFuincTable, const BOOL_P blpThrowExceptionIfFailed);

protected:
    CMUIntPArray m_aryLibHandles;  // 记录所有被载入库的句柄
};

//-----------------------------------------------------------------------------------------------

class CWinSockIniter : public CVolCommonBase
{
public:
    inline_ CWinSockIniter ()
    {
        m_blpWinSockInited = FALSE;
    }

    inline_ ~CWinSockIniter ()
    {
        Cleanup ();
    }

public:
    BOOL_P InitWinSock ();
    void Cleanup ();

protected:
    BOOL_P m_blpWinSockInited;  // 是否初始化了WinSock
};

//-----------------------------------------------------------------------------------------------

// _NAME_COMPILER_AGREED (_DPISIZE)
#ifdef _VOL_HIGH_DPI  // 需要支持高DPI下自动缩放界面(由编译器自动根据项目选项进行提供)?
    #define _DPISIZE(size)  g_objVolApp.MulDPI (size)
#else
    #define _DPISIZE(size)  size
#endif

// 火山用户程序实例信息
class _NAME_COMPILER_AGREED (CVolAppInstance): public CVolCommonBase
{
public:
    CVolAppInstance ();
    ~CVolAppInstance ();

    // 初始化本对象的内容,火山程序启动模块必须在程序启动后最先调用本方法.
    void _NAME_COMPILER_AGREED (init) (const HMODULE hInstance, const INT_P npArgC, const TCHAR** aszArgV, CVolRuntimeClass* pVolAppRuntimeClass);
    void OnBeforeExit ();
    void OnIdle ();

public:
    // 返回用户火山程序启动类对象
    inline_ CVolUserApp& GetVolApp ()
    {
        ASSERT (m_pVolAppObject != NULL);  // 必定已经被初始化
        return *m_pVolAppObject;
    }

    // 初始化外部函数表,返回是否成功.
    inline_ BOOL_P _NAME_COMPILER_AGREED (InitExternFuncTable) (EXTERN_FUNC_ITEM* pExternFuincTable, const BOOL_P blpThrowExceptionIfFailed)
    {
        return m_objDllLoader.InitExternFuncTable (pExternFuincTable, blpThrowExceptionIfFailed);
    }

    inline_ BOOL_P InitWinSock ()
    {
        return m_objWinSockIniter.InitWinSock ();
    }

    // 返回当前模块的实例句柄
    // 注意: 不要直接使用此实例句柄去载入相关资源,载入资源请使用下面的"资源载入相关"系列方法,它们支持在设计器中使用.
    virtual HMODULE _NAME_COMPILER_AGREED (GetInstanceHandle) () const;

    // 返回启动命令行中的参数数目
    inline_ INT_P _NAME_COMPILER_AGREED (GetArgCount) () const
    {
        return m_npArgC;
    }

    // 返回当前程序是否为DLL
    inline_ BOOL_P IsDllModule () const
    {
    #ifdef _USRDLL
        return TRUE;
    #else
        return FALSE;
    #endif
    }

    // 返回启动命令行中指定索引位置处的参数文本
    inline_ const TCHAR* _NAME_COMPILER_AGREED (GetArg) (const INT_P npArgIndex) const
    {
        ASSERT (npArgIndex >= 0 && npArgIndex < m_npArgC);
        return m_aszArgV [npArgIndex];
    }

    // 返回当前所编译的版本是否为界面设计器专用版.
    // 在程序其它位置如果不想通过 _VOL_FOR_UI_DESIGNER 判断,可以调用本方法.
    virtual BOOL_P IsForUiDesigner () const
    {
        return
        #ifdef _VOL_FOR_UI_DESIGNER
            TRUE;
        #else
            FALSE;
        #endif
    }

    // 返回用于快速分配内存的缓存池类对象
    inline_ CPoolMem* GetPoolMem ()
    {
    #ifdef _DEBUG
        // 本对象必定处于已经被构造且尚未被销毁状态
        assert (m_npObjectState == 1);  // 注意此处不能使用ASSERT,因为里面内部构造错误报告信息时会又去分配内存.
    #endif
        return &m_memPool;
    }

    // 返回系统主屏幕DPI比例
    inline_ DOUBLE GetDPI () const
    {
        return m_dbDPI;
    }

    // 将指定尺寸值乘于系统主屏幕DPI比例后返回结果值
    inline_ INT MulDPI (const INT nSize) const
    {
        return RoundDoubleToInt ((DOUBLE)nSize * m_dbDPI);
    }

    // 将指定尺寸值除于系统主屏幕DPI比例后返回结果值
    inline_ INT DivDPI (const INT nSize) const
    {
        return RoundDoubleToInt ((DOUBLE)nSize / m_dbDPI);
    }

    // 返回默认字体句柄
    inline_ HFONT GetDefaultFont () const
    {
        return (HFONT)::GetStockObject (DEFAULT_GUI_FONT);
    }

    // 预先过滤处理输入信息,返回是否已经处理.
    static BOOL_P sVolPreFilterInputMessage (const MSG* pMsg);

    // 返回指定消息是否会被 sVolPreFilterInputMessage 检查处理
    inline_ static BOOL_P sIsVolPreFilterInputMessage (UINT message)
    {
        return ((message >= WM_MOUSEFIRST && message <= WM_MOUSELAST) ||
                (message >= WM_KEYFIRST && message <= WM_KEYLAST));
    }

    // 设置所指定句柄的窗口需要预先过滤处理输入信息
    static void sSetWndNeedPreFilterInputMessage (HWND hWnd)
    {
        ASSERT (hWnd != NULL);
        ::SetWindowLongPtr (hWnd, GWLP_USERDATA, (LONG_PTR)VWD_INPUT_MSG_FILTER_MARK);
    }

    // 如果hWnd所对应对象的类型为szClassName,则返回该窗口对象指针,否则返回NULL.
    static void* sGetWndObject (HWND hWnd, const TCHAR* szClassName);
    // 在hWnd及其所有直接/间接父窗口中查找类型为szFindClassName的父窗口对象指针,找到该对象指针,否则返回NULL.
    static void* sFindParentWndObjectWithSpecClass (HWND hWnd, const TCHAR* szFindClassName);

    //----------------------------------------------------------  资源载入相关
    // 在火山程序中载入相关资源必须使用下列方法,使用这些方法可以支持SetResourceRedirect所指定的资源转向,以支持在布局设计器中写入相关火山对象属性.

    // 载入所指定的字符串资源,返回对应的文本.
    //   upResID: 所欲载入图像的资源ID,为0表示为空资源.
    //   strRes: 用作保存所载入的字符串文本
    virtual CVolString& LoadResString (const UINT_P upResID, CVolString& strRes);

    // 载入所指定的图像资源,成功返回对应句柄,失败返回NULL.
    //   enType: 所载入图像的类型
    //   upResID: 所欲载入图像的资源ID,为0表示为空资源.
    //   注意: 所载入的 VRIT_CURSOR / VRIT_ICON 类型图像资源不需要释放,所载入的 VRIT_BITMAP 资源在不使用后需要使用 ::DeleteObject 释放,
    // 所载入的 VRIT_IMAGE_LIST 资源在不使用后需要使用 ::ImageList_Destroy 释放.
    virtual HANDLE LoadResImage (const VOL_RES_IMAGE_TYPE enImageType, const UINT_P upResID);

    // 载入所指定的图像文件,成功返回对应句柄,失败返回NULL.
    //   enType: 所载入图像的类型
    //   szImageFileName: 所欲载入图像的文件名
    // 注意: 所载入的资源在不需要使用后需要将其释放
    virtual HANDLE LoadResImageFile (const VOL_RES_IMAGE_TYPE enImageType, const TCHAR* szImageFileName);

    // 从内存中载入所指定的图像数据,成功返回对应句柄,失败返回NULL.
    virtual HBITMAP LoadBitmapFromMemory (const BYTE* pBitmapData, const INT_P npBitmapDataSize);

    inline_ HBITMAP LoadBitmapFromMemory (const CVolMem& memBitmapData)
    {
        return LoadBitmapFromMemory (memBitmapData.GetPtr (), memBitmapData.GetSize ());
    }

    // 将指定的类型为RCDATA的资源内容载入到memRes中,返回是否成功.
    //   upResID: 所欲载入资源的ID,为0表示为空资源.
    virtual BOOL_P _NAME_COMPILER_AGREED (LoadResData) (const UINT_P upResID, CVolMem& memRes)
    {
        return LoadResData (upResID, memRes, RT_RCDATA);
    }

    // 将指定的类型为RCDATA的Unicode文本资源内容载入到strRes中,返回是否成功.
    //   upResID: 所欲载入资源的ID,为0表示为空资源.
    virtual BOOL_P _NAME_COMPILER_AGREED (LoadResData) (const UINT_P upResID, CVolString& strRes);

    // 将所指定类型的资源内容载入到memRes中,返回是否成功.
    //   upResID: 所欲载入资源的ID,为0表示为空资源.
    virtual BOOL_P LoadResData (const UINT_P upResID, CVolMem& memRes, const TCHAR* szResType);

#ifdef _VOL_FOR_UI_DESIGNER
    // 设置下一次 LoadResImage / LoadResData 调用需要转向载入的资源文件或者下一次 LoadResString 调用所需要转向的文本字符串
    //   szResourceRedirect: 转向文本,为NULL表示取消转向.
    inline_ void _NAME_COMPILER_AGREED (SetResourceRedirect) (const TCHAR* szResourceRedirect)
    {
        m_szResourceRedirect = szResourceRedirect;
    }
#endif

    inline_ BOOL_P InitGDIPlus ()
    {
        return m_objGDIPlus.init ();
    }

    inline_ void CleanupGDIPlus ()
    {
        m_objGDIPlus.Cleanup ();
    }

    // 如果当前为编译DLL,则清理GDI+,避免在DllMain中清理(会出错).
    // Do not call GdiplusStartup or GdiplusShutdown in DllMain or in any function that is called by DllMain.
    inline_ void DllCleanupGDIPlus ()
    {
    #ifdef _USRDLL
        m_objGDIPlus.Cleanup ();
    #endif
    }

    //----------------------------------------------------------

    inline_ void SetDevMode (const HGLOBAL hDevMode, const BOOL_P blpFreeOld = TRUE)
    {
        SetHGlobal (0, hDevMode, blpFreeOld);
    }
    inline_ HGLOBAL GetDevMode () const
    {
        return GetHGlobal (0);
    }

    inline_ void SetDevNames (const HGLOBAL hDevMode, const BOOL_P blpFreeOld = TRUE)
    {
        SetHGlobal (1, hDevMode, blpFreeOld);
    }
    inline_ HGLOBAL GetDevNames () const
    {
        return GetHGlobal (1);
    }

    // 返回全局线程池
    inline_ CVolThreadPool& GetThreadPool ()
    {
        return m_objThreadPool;
    }

    // 返回具有所指定类型的唯一性全局对象,如果该类对象不存在,将自动创建.
    // 所有全局对象将会在用户程序退出时被自动销毁.
    CVolObject* GetGlobalObject (const CVolRuntimeClass* pRuntimeClass);

    inline_ CVolObject& GetRefGlobalObject (const CVolRuntimeClass* pRuntimeClass)
    {
        return *GetGlobalObject (pRuntimeClass);
    }

    // 创建一个始终隐藏的窗口,该类窗口一般用作接收消息用.
    //   szClassName: 窗口类名,必须有效且不为空文本.
    //   lpfnWndProc: 窗口消息接收函数,为NULL表示使用Windows默认消息接收函数.
    //   hParentWnd: 父窗口句柄,为NULL表示无.
    HWND CreateHiddenWindow (const TCHAR* szClassName, WNDPROC lpfnWndProc, HWND hParentWnd);

    inline_ INT GetMainThreadID () const
    {
        return (INT)m_dwMainThreadID;
    }

protected:
    void SetHGlobal (const INT_P npIndex, const HGLOBAL hGlobal, const BOOL_P blpFreeOld);
    
    inline_ HGLOBAL GetHGlobal (const INT_P npIndex) const
    {
        ASSERT (npIndex >= 0 && npIndex < NUM_ELEMENTS_OF (m_ahGlobals));
        return m_ahGlobals [npIndex];
    }

    //----------------------------------------------------------

private:
    CPoolMem m_memPool;  // 用于快速分配内存的缓存池类对象
    CExternFunctionLoader m_objDllLoader;  // 外部函数载入器
    CWinSockIniter m_objWinSockIniter;  // Winsock初始化
    CVolUserApp* m_pVolAppObject;  // 用作记录用户火山程序启动类对象,初始化后必定不为NULL.
    BOOL_P m_blpComInitSucceeded;  // 是否成功初始化了COM
    DOUBLE m_dbDPI;  // 程序启动时的屏幕DPI
    CInitGDIPlus m_objGDIPlus;
    HGLOBAL m_ahGlobals [2];  // 用作保存相关全局内存句柄
    CVolThreadPool m_objThreadPool;  // 全局线程池

    CMMutex m_mxAccess;  // 全局数据访问锁
    CVolObjectArray m_aryGlobalObjects;  // 记录所有全局对象

    HMODULE m_hInstance;  // 当前程序的实例句柄,如果为NULL表示尚未设置.
    INT_P m_npArgC;  // 启动程序时所提供的启动参数数目
    const TCHAR** m_aszArgV;  // 启动程序时所提供的启动参数文本数组,该数组有效成员数为m_npArgC.
    DWORD m_dwMainThreadID;  // 主线程ID

#ifdef _VOL_FOR_UI_DESIGNER
    // 资源载入转向:
    const TCHAR* m_szResourceRedirect;  // 资源转向文本(正在转向载入的资源文件名/字符串)
    CMStringArray m_saryCachedImageFileNames;  // 所已经载入的图像资源的文件名
    CMUIntPArray m_uaryCachedImageHandles;  // 所已经载入的图像资源的句柄
    CMIntPArray m_naryCachedImageTypes;  // 所已经载入的图像资源的类型(VRIT_CURSOR / VRIT_ICON)
#endif

#ifdef _DEBUG
    INT_P m_npObjectState;  // 用作标记本对象的当前状态: 0:尚未构造; 1:已经构造; -1:已经被销毁
#endif

    friend class CVolUserApp;
};

// 火山程序启动模块必须在程序启动时调用 g_objVolApp.init 方法初始化该对象.
extern CVolAppInstance _NAME_COMPILER_AGREED (g_objVolApp);

//--------------------------------------------------------------------------------------

class IVolWndMsgFilter
{
public:
    virtual void OnFilterMessage (UINT uMsg, WPARAM wParam, LPARAM lParam) = 0;
};

template <UINT uFilterMessageFirst, UINT uFilterMessageLast>
class CVolMsgFilterWindow : public CVolCommonBase
{
    #define _T_VOL_MSG_FILTER_WINDOW_CLASS_NAME _T ("_VOL_CVolMsgFilterWindow")

public:
    inline_ CVolMsgFilterWindow (IVolWndMsgFilter* pMsgFilter) : m_pMsgFilter (pMsgFilter)
    {
        ASSERT (pMsgFilter != NULL && uFilterMessageLast >= uFilterMessageFirst);
        m_hWnd = NULL;
    }

    inline_ ~CVolMsgFilterWindow ()
    {
        Destroy ();
    }

public:
    HWND Create ()
    {
        if (m_hWnd != NULL)
            return m_hWnd;

        TCHAR acClassName [NUM_ELEMENTS_OF (_T_VOL_MSG_FILTER_WINDOW_CLASS_NAME) + 64];
        wsprintf (acClassName,_T_VOL_MSG_FILTER_WINDOW_CLASS_NAME _T ("_%X_%X"), (INT)uFilterMessageFirst, (INT)uFilterMessageLast);

        m_hWnd = g_objVolApp.CreateHiddenWindow (acClassName, (WNDPROC)sVolWindowProc, NULL);
        if (m_hWnd != NULL && ::SetProp (m_hWnd, _T_VOL_MSG_FILTER_WINDOW_CLASS_NAME, (HANDLE)this) == FALSE)
        {
            ::DestroyWindow (m_hWnd);
            m_hWnd = NULL;
        }

        return m_hWnd;
    }

    inline_ void Destroy ()
    {
        if (m_hWnd != NULL)
        {
            if (::IsWindow (m_hWnd))
            {
                ::RemoveProp (m_hWnd, _T_VOL_MSG_FILTER_WINDOW_CLASS_NAME);
                ::DestroyWindow (m_hWnd);
            }
            m_hWnd = NULL;
        }
    }

    inline_ HWND GetWndHandle () const
    {
        return m_hWnd;
    }

protected:
    static LRESULT CALLBACK sVolWindowProc (HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
    {
        if (uMsg >= uFilterMessageFirst && uMsg <= uFilterMessageLast)
        {
            CVolMsgFilterWindow* pThis = (CVolMsgFilterWindow*)::GetProp (hWnd, _T_VOL_MSG_FILTER_WINDOW_CLASS_NAME);

            if (pThis != NULL)
                pThis->m_pMsgFilter->OnFilterMessage (uMsg, wParam, lParam);
        }

        if (uMsg == WM_NCDESTROY)
            ::RemoveProp (hWnd, _T_VOL_MSG_FILTER_WINDOW_CLASS_NAME);

        return DefWindowProc (hWnd, uMsg, wParam, lParam);
    }

protected:
    IVolWndMsgFilter* const m_pMsgFilter;
    HWND m_hWnd;
};

//--------------------------------------------------------------------------------------

class IVolWindowProcFilter
{
public:
    // 在消息默认处理程序之前调用
    // 返回真表示已经被处理且不需要向后继续传递,返回假表示未被处理.
    virtual BOOL_P FilterBeforeDefProc (HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam, LRESULT& lResult)  { return FALSE; }

    // 在消息默认处理程序之后调用
    // virtual BOOL_P FilterAfterDefProc (HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam, LRESULT& lResult)  { return FALSE; }
};

typedef struct VOL_WIN_PROC_FILTER_INFO
{
    IVolWindowProcFilter* m_pMsgFilter;
    VOL_WIN_PROC_FILTER_INFO* m_pinfNextFilter;
}
VOL_WIN_PROC_FILTER_INFO;

class CVolWindowProcFilters : public CVolCommonBase
{
public:
    inline_ CVolWindowProcFilters ()
    {
        m_pinfFirstFilter = NULL;
    }

    inline_ ~CVolWindowProcFilters ()
    {
        Cleanup ();
    }

    virtual void Cleanup ();

public:
    virtual void RegisterFilter (IVolWindowProcFilter* pMsgFilter);
    virtual BOOL_P UnregisterFilter (IVolWindowProcFilter* pMsgFilter);
    virtual BOOL_P CallFilterBeforeDefProc (HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam, LRESULT& lResult);
    // virtual BOOL_P CallFilterAfterDefProc (HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam, LRESULT& lResult);

    inline_ static BOOL_P sRegisterFilter (HWND hWndHook, IVolWindowProcFilter* pMsgFilter)
    {
        ASSERT (hWndHook != NULL && pMsgFilter != NULL);
        return (::SendMessage (hWndHook, MWM_REGISTER_WINDOW_PROC_FILTER, (WPARAM)pMsgFilter, _VOL_MSG_ACK) == _VOL_MSG_ACK);
    }

    inline_ static BOOL_P sUnregisterFilter (HWND hWndHook, IVolWindowProcFilter* pMsgFilter)
    {
        ASSERT (hWndHook != NULL);
        return (::SendMessage (hWndHook, MWM_UNREGISTER_WINDOW_PROC_FILTER, (WPARAM)pMsgFilter, _VOL_MSG_ACK) == _VOL_MSG_ACK);
    }

protected:
    VOL_WIN_PROC_FILTER_INFO* m_pinfFirstFilter;
};

#endif
