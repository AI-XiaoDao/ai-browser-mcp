
// Copyright (C) Recursion Company. All rights reserved.

#include "../vol_base.h"

// 本实例变量不在此处定义,由火山程序编译器与用户程序中的所有静态变量放置在一起,以确定构造和析构顺序.
// CVolAppInstance g_objVolApp;  // 火山用户程序信息的全局唯一性实例

//----------------------------------------------------------------------------------------------

CVolUserApp::CVolUserApp ()
{
    ASSERT (g_objVolApp.m_pVolAppObject == NULL);  // 本对象实例必须是单例的
    g_objVolApp.m_pVolAppObject = this;
}

CVolUserApp::SPEC_USER_CLASS_TYPE CVolUserApp::FindSpecialUserClassType (const CVolObject* pVolObject) const
{
    ASSERT (pVolObject != NULL);

    const CVolRuntimeClass** apVolRuntimeClass = GetSpecialUserRuntimeClasses ();

    if (apVolRuntimeClass != NULL)
    {
        for (INT_P npIndex = 0; npIndex < _NUM_SPEC_USER_CLASS_TYPES; npIndex++)
        {
            ASSERT (apVolRuntimeClass [npIndex] != NULL);

            if (pVolObject->IsVolInstanceOf (apVolRuntimeClass [npIndex]))
                return (SPEC_USER_CLASS_TYPE)npIndex;
        }
    }
    ELSE_FAIL  // 正常情况下不可能为NULL,必定已经被覆盖处理.

    return SUCT_UNKNOWN;
}

//----------------------------------------------------------------------------------------------

void CVolObject::GetDumpString (CVolString& strDump, INT nMaxDumpSize)
{
    strDump.AddFormatText (_T_UNKNOWN_DUMPING_VOL_OBJECT_SX, CVolString (GetRuntimeClass ()->GetClassFullName ()).GetText (), (UINT_P)this);

    if (IsNullObject ())
        strDump.AddText (_T_EMPTY_VOL_OBJECT);
}

//----------------------------------------------------------------------------------------------

BOOL CRefObject::Release ()
{
    ASSERT (m_npRefCount > 0);

#if defined (_PF_WIN32)
    _asm mov eax, [this]
    _asm lock dec dword ptr [eax + m_npRefCount]
    _asm jg quit
    OnBeforeDestory ();
    delete this;
    return TRUE;
quit:
    return FALSE;
#elif defined (_PF_WIN64)
    if (_InterlockedDecrement64 ((LONGLONG*)&m_npRefCount) == 0)
    {
        OnBeforeDestory ();
        delete this;
        return TRUE;
    }
    else
        return FALSE;
#elif defined (_PF_LINUX)
    #if defined (_PF_LINUX32)
        __asm__ __volatile__  ("lock decl %0": "=m"(m_npRefCount));
    #elif defined (_PF_LINUX64)
        __asm__ __volatile__  ("lock decq %0": "=m"(m_npRefCount));
    #else
        #error Not be supported.
    #endif
        __asm__ __volatile__  ("jg 1f")
            OnBeforeDestory ();
            delete this;
            return TRUE;
        __asm__ __volatile__  ("1:")
            return FALSE;
#else
    #error Not be supported.
#endif
}

//----------------------------------------------------------------------------------------------

void CVolRefObject::_CopySelfFrom (const CVolRefObject& objCopyFrom)
{
    SetRefObject (objCopyFrom.m_pRefObject);
}

BOOL CVolRefObject::_IsSelfEqual (const CVolRefObject& objCompare) const
{
    return (m_pRefObject == objCompare.m_pRefObject);
}

void CVolRefObject::SetRefObject (CRefObject* pRefObject)
{
    ASSERT_R_DATA_OR_NULL (pRefObject);

    if (pRefObject != NULL)
        pRefObject->AddRef ();

    if (m_pRefObject != NULL)
        m_pRefObject->Release ();

    m_pRefObject = pRefObject;
}

void CVolRefObject::TakeOverNewRefObject (CRefObject* pNewRefObject)
{
    ASSERT (pNewRefObject != m_pRefObject);  // pNewRefObject应该是一个新建的对象
    ASSERT_R_DATA_OR_NULL (pNewRefObject);

    if (m_pRefObject != NULL)
        m_pRefObject->Release ();

    m_pRefObject = pNewRefObject;
}

//----------------------------------------------------------------------------------------------

void CVolWrapperObject::_CopySelfFrom (const CVolWrapperObject& objCopyFrom)
{
    CRefObjectWithData<CVolObjectDestroyer>* pRefObject = objCopyFrom.m_pRefObject;

    if (pRefObject != NULL)
        pRefObject->AddRef ();

    if (m_pRefObject != NULL)
        m_pRefObject->Release ();

    m_pRefObject = pRefObject;
}

BOOL CVolWrapperObject::_IsSelfEqual (const CVolWrapperObject& objCompare) const
{
    return (m_pRefObject == objCompare.m_pRefObject);
}

void CVolWrapperObject::GetDumpString (CVolString& strDump, INT nMaxDumpSize)
{
    CVolObject* pobjWrapped = GetVolObjectPointer ();

    if (pobjWrapped == NULL)
        strDump.AddText (_T_NULL_VOL_OBJECT);
    else
        pobjWrapped->GetDumpString (strDump, nMaxDumpSize);
}

CVolObject& CVolWrapperObject::TakeOverVolObject (CVolObject* pobjWrapped)
{
    ASSERT (pobjWrapped != NULL);

    if (m_pRefObject == NULL)
        m_pRefObject = new CRefObjectWithData<CVolObjectDestroyer>;

    m_pRefObject->m_data.SetVolObject (pobjWrapped);
    ASSERT (GetVolObjectPointer () == pobjWrapped);

    return *pobjWrapped;
}

//----------------------------------------------------------------------------------------------

#pragma comment(lib, "ws2_32.lib")

BOOL_P CWinSockIniter::InitWinSock ()
{
    if (m_blpWinSockInited == FALSE)
    {
        WSADATA wsaData;
        m_blpWinSockInited = (WSAStartup (MAKEWORD (1, 1), &wsaData) == 0);
    }

    return m_blpWinSockInited;
}

void CWinSockIniter::Cleanup ()
{
    if (m_blpWinSockInited)
    {
        WSACleanup ();
        m_blpWinSockInited = FALSE;
    }
}

//----------------------------------------------------------------------------------------------

CVolAppInstance::CVolAppInstance () :
        m_memPool (_VOL_MEM_POOL_BLOCK_SIZE * 256, _VOL_NUM_MEM_POOL_BLOCKS)
{
    m_pVolAppObject = NULL;
    m_hInstance = NULL;
    m_npArgC = 0;
    m_aszArgV = NULL;
    m_dwMainThreadID = 0;
    m_blpComInitSucceeded = FALSE;
    m_dbDPI = 1.0;
    ZERO_MEM (m_ahGlobals, sizeof (m_ahGlobals));

#ifdef _VOL_FOR_UI_DESIGNER
    m_szResourceRedirect = NULL;
#endif

#ifdef _DEBUG
    ASSERT (m_npObjectState == 0);  // 全局变量的初始值均为0
    m_npObjectState = 1;  // 设置本对象为已经被构造状态
#endif
}

// 注意: 本方法中的代码能够确保在静态用户程序数据销毁后才会被调用
CVolAppInstance::~CVolAppInstance ()
{
    m_objThreadPool.Cleanup ();  // 清理全局线程池

    INT_P npIndex;
#ifdef _VOL_FOR_UI_DESIGNER
    const INT_P npNumResFiles = m_saryCachedImageFileNames.GetCount ();
    ASSERT (m_uaryCachedImageHandles.GetCount () == npNumResFiles &&
            m_naryCachedImageTypes.GetCount () == npNumResFiles);

    // 删除所有被载入的图像句柄
    for (npIndex = 0; npIndex < npNumResFiles; npIndex++)
    {
        if (m_naryCachedImageTypes [npIndex] == VRIT_CURSOR)
        {
            VERIFY (::DestroyCursor ((HCURSOR)m_uaryCachedImageHandles [npIndex]));
        }
        else
        {
            ASSERT (m_naryCachedImageTypes [npIndex] == VRIT_ICON);  // 唯一剩余的可能
            VERIFY (::DestroyIcon ((HICON)m_uaryCachedImageHandles [npIndex]));
        }
    }

    m_saryCachedImageFileNames.RemoveAll ();
    m_uaryCachedImageHandles.RemoveAll ();
    m_naryCachedImageTypes.RemoveAll ();
#endif

    // 销毁所记录的火山程序启动类对象
    if (m_pVolAppObject != NULL)
    {
        m_pVolAppObject->Destroy ();
        m_pVolAppObject = NULL;
    }

    m_aryGlobalObjects.RemoveAll ();  // 删除所有全局对象

    if (m_blpComInitSucceeded)
    {
        m_blpComInitSucceeded = FALSE;
        CoUninitialize ();
    }

    m_objWinSockIniter.Cleanup ();

    CleanupGDIPlus ();

    // 释放可能存在的全局句柄
    for (npIndex = 0; npIndex < NUM_ELEMENTS_OF (m_ahGlobals); npIndex++)
        GlobalUnlockAndFree (m_ahGlobals [npIndex]);

    m_objDllLoader.Cleanup ();

#ifdef _DEBUG
    m_npObjectState = -1;  // 设置本对象为已经被销毁状态
#endif
}

void CVolAppInstance::OnIdle ()
{
    m_objThreadPool.UpdatePool (FALSE);  // 更新全局线程池
}

void CVolAppInstance::OnBeforeExit ()
{
    m_objThreadPool.Cleanup ();  // 清理全局线程池

    // 销毁所记录的火山程序启动类对象
    if (m_pVolAppObject != NULL)
    {
        m_pVolAppObject->Destroy ();
        m_pVolAppObject = NULL;
    }

    m_aryGlobalObjects.RemoveAll ();  // 删除所有全局对象
    m_objDllLoader.Cleanup ();
    CleanupGDIPlus ();  // 因为GDI+的清理工作不支持在DLL的卸载函数中执行,因此此处必须提前清理,避免所编译出来的用户动态链接库出问题.
}

CVolObject* CVolAppInstance::GetGlobalObject (const CVolRuntimeClass* pRuntimeClass)
{
    ASSERT_R_DATA (pRuntimeClass);

    m_mxAccess.lock ();

    const INT_P npCount = m_aryGlobalObjects.GetCount ();
    for (INT_P npIndex = 0; npIndex < npCount; npIndex++)
    {
        if (m_aryGlobalObjects.GetPtrAt (npIndex)->IsVolInstanceOf (pRuntimeClass))
        {
            CVolObject* pVolObject = m_aryGlobalObjects.GetPtrAt (npIndex);
            m_mxAccess.unlock ();
            return pVolObject;
        }
    }

    m_mxAccess.unlock ();
    CVolObject* pVolObject = pRuntimeClass->CreateObject ();

    m_mxAccess.lock ();
    m_aryGlobalObjects.AddTakeOverObject (pVolObject);
    m_mxAccess.unlock ();

    return pVolObject;
}

// 初始化本对象的内容,火山程序启动模块必须在程序启动时调用本方法.
void CVolAppInstance::init (const HMODULE hInstance, const INT_P npArgC, const TCHAR** aszArgV, CVolRuntimeClass* pVolAppRuntimeClass)
{
    ASSERT (pVolAppRuntimeClass != NULL && hInstance != NULL && npArgC >= 0 && m_hInstance == NULL &&
            m_pVolAppObject == NULL && m_blpComInitSucceeded == FALSE);  // 只允许初始化一次

    m_hInstance = hInstance;
    m_npArgC = npArgC;
    m_aszArgV = aszArgV;
    m_dwMainThreadID = ::GetCurrentThreadId ();

    m_blpComInitSucceeded = SUCCEEDED (::CoInitializeEx (NULL, COINIT_APARTMENTTHREADED));
#ifdef _VOL_HIGH_DPI  // 需要支持高DPI下自动缩放界面(由编译器自动根据项目选项进行提供)?
    MSetProcessDpiAwareness (2);  // PROCESS_PER_MONITOR_DPI_AWARE
#endif
    m_dbDPI = GetMoniterDPI (NULL);

    // 必须放在最后,以防用户程序在类的构造方法中访问前面的信息.
    m_pVolAppObject = (CVolUserApp*)pVolAppRuntimeClass->CreateObject ();

    if (P_IS_VOL_INSTANCE_OF (m_pVolAppObject, CVolUserApp) == FALSE)
    {
        m_pVolAppObject->Destroy ();
        FAIL;
        exit (-1);
    }
}

HMODULE CVolAppInstance::GetInstanceHandle () const
{
    return (m_hInstance != NULL ? m_hInstance : GetSelfModuleHandle ());
}

static HIMAGELIST sCreateImageListFromBitmap (const HBITMAP hBitmap)
{
    CMSize sizeItem;
    if (GetImageListItemSize (hBitmap, &sizeItem) == FALSE)
        return NULL;

    const HIMAGELIST hImageList = ::ImageList_Create (sizeItem.cx, sizeItem.cy, (ILC_COLOR32 | ILC_MASK), 0, 1);
    if (hImageList == NULL)
        return NULL;

    if (::ImageList_AddMasked (hImageList, hBitmap, VIL_TRANSPARENT_COLOR) < 0)
    {
        ::ImageList_Destroy (hImageList);
        return NULL;
    }

    return hImageList;
}

HANDLE CVolAppInstance::LoadResImageFile (const VOL_RES_IMAGE_TYPE enImageType, const TCHAR* szImageFileName)
{
    ASSERT_R_STR (szImageFileName);

    HANDLE hRes = NULL;
    if (IsEmptyStr (szImageFileName) == FALSE)
    {
        if (enImageType == VRIT_BITMAP || enImageType == VRIT_IMAGE_LIST)
        {
            CVolImage objImage;
            if (objImage.LoadFromFile (szImageFileName) == FALSE)
                return NULL;

            hRes = objImage.Detach ();
        }
        else
        {
            UINT uType;
            switch (enImageType)
            {
            case VRIT_CURSOR:
                uType = IMAGE_CURSOR;
                break;
            case VRIT_ICON:
                uType = IMAGE_ICON;
                break;
            default:
                FAIL;
                return NULL;
            }

            hRes = ::LoadImage (0, szImageFileName, uType, 0, 0, LR_LOADFROMFILE);
        }

        if (enImageType == VRIT_IMAGE_LIST && hRes != NULL)
        {
            const HIMAGELIST hImageList = sCreateImageListFromBitmap ((HBITMAP)hRes);
            VERIFY (::DeleteObject ((HBITMAP)hRes));
            hRes = hImageList;
        }
    }

    return hRes;
}

BOOL_P CVolAppInstance::sVolPreFilterInputMessage (const MSG* pMsg)
{
    ASSERT (pMsg != NULL);

    // 处理输入信息过滤
    if (sIsVolPreFilterInputMessage (pMsg->message))
    {
        HWND hWnd = pMsg->hwnd;

        do
        {
            if ((UINT_P)::GetWindowLongPtr (hWnd, GWLP_USERDATA) == VWD_INPUT_MSG_FILTER_MARK)  // 需要过滤输入消息?
            {
                if (::SendMessage (hWnd, MWM_PRE_FILTER_INPUT_MSG, (WPARAM)pMsg, _VOL_MSG_ACK) == _VOL_MSG_ACK)  // 已经被过滤掉了?
                    return TRUE;
            }

            if (((UINT_P)::GetWindowLongPtr (hWnd, GWL_STYLE) & WS_CHILD) == 0)  // 不为子窗口?
                break;

            hWnd = ::GetParent (hWnd);
        }
        while (hWnd != NULL);
    }

    return FALSE;
}

void* CVolAppInstance::sGetWndObject (HWND hWnd, const TCHAR* szClassName)
{
    ASSERT (hWnd != NULL && IsEmptyStr (szClassName) == FALSE);

    _VOL_GET_WND_OBJECT_PARAM param;
    param.m_szFindClassName = szClassName;
    param.m_pWndObject = NULL;

    return (::SendMessage (hWnd, MWM_GET_WND_OBJECT, (WPARAM)&param, _VOL_MSG_ACK) == _VOL_MSG_ACK ?  // 获取成功?
            param.m_pWndObject : NULL);
}

void* CVolAppInstance::sFindParentWndObjectWithSpecClass (HWND hWnd, const TCHAR* szFindClassName)
{
    ASSERT (IsEmptyStr (szFindClassName) == FALSE);

    while (hWnd != NULL)
    {
        void* pWndObject = sGetWndObject (hWnd, szFindClassName);
        if (pWndObject != NULL)
            return pWndObject;

        hWnd = ::GetParent (hWnd);
    }

    return NULL;
}

HWND CVolAppInstance::CreateHiddenWindow (const TCHAR* szClassName, WNDPROC lpfnWndProc, HWND hParentWnd)
{
    ASSERT (IsEmptyStr (szClassName) == FALSE);

    const HINSTANCE hInstance = GetInstanceHandle ();

    WNDCLASS wndcls;
    if (::GetClassInfo (hInstance, szClassName, &wndcls) == FALSE)  // 尚不存在?
    {
        ZERO_MEM (&wndcls, sizeof (wndcls));
        wndcls.lpfnWndProc = (lpfnWndProc == NULL ? ::DefWindowProc : lpfnWndProc);
        wndcls.hInstance = hInstance;
        wndcls.hCursor = ::LoadCursor (NULL, IDC_ARROW);
        wndcls.hbrBackground = (HBRUSH)::GetStockObject (NULL_BRUSH);
        wndcls.lpszClassName = szClassName;

        if (::RegisterClass (&wndcls) == FALSE)
            return NULL;
    }

    return ::CreateWindowEx (WS_EX_TOOLWINDOW, szClassName, _T (""), 0, 0, 0, 0, 0, hParentWnd, NULL, hInstance, NULL);
}

void CVolAppInstance::SetHGlobal (const INT_P npIndex, const HGLOBAL hGlobal, const BOOL_P blpFreeOld)
{
    ASSERT (npIndex >= 0 && npIndex < NUM_ELEMENTS_OF (m_ahGlobals));

    if (m_ahGlobals [npIndex] != hGlobal)
    {
        if (blpFreeOld)
            GlobalUnlockAndFree (m_ahGlobals [npIndex]);

        m_ahGlobals [npIndex] = hGlobal;
    }
}

HIMAGELIST CreateImageListFromBitmapData (const BYTE* pBitmapData, const INT_P npBitmapDataSize)
{
    CVolImage objImage;
    if (objImage.LoadFromMemory (pBitmapData, npBitmapDataSize) == FALSE)
        return NULL;

    return sCreateImageListFromBitmap (objImage.GetBitmapHandle ());
}

CVolString& CVolAppInstance::LoadResString (const UINT_P upResID, CVolString& strRes)
{
#ifdef _VOL_FOR_UI_DESIGNER
    if (m_szResourceRedirect != NULL)  // 转向为所指定文本?
    {
        strRes.SetText (m_szResourceRedirect);  // 直接设置为所转向到的文本
        m_szResourceRedirect = NULL;  // 取消后续转向
        return strRes;
    }
#endif

    strRes.Empty ();
    if (upResID != 0)  // 不为空资源?
    {
        const HMODULE hInstance = GetInstanceHandle ();

        #ifdef _UNICODE
            #define _CHAR_FUDGE 1  // one TCHAR unused is good enough
        #else
            //   当编译非Unicode版本时(DBCS),只有多余2个字符(一个结束零字符,另一个用作避免载入DBCS的半个汉字)
            // 才能确定没有剩余的字符串未载入.
            #define _CHAR_FUDGE 2  // two BYTES unused for case of DBC last char
        #endif

        TCHAR buf [4097 + 3];  // 根据MS的文档,字符串资源的最大允许长度为 4097
        INT_P npLen = ::LoadString (hInstance, (UINT)upResID, buf, NUM_ELEMENTS_OF (buf));

        if (npLen > 0)  // 载入成功?
        {
            if (NUM_ELEMENTS_OF (buf) - npLen > _CHAR_FUDGE)
            {
                strRes.SetText (buf);
            }
            else
            {
                CVolMem memBuf;
                INT_P npSize = NUM_ELEMENTS_OF (buf);

                do
                {
                    npSize += NUM_ELEMENTS_OF (buf);
                    npLen = ::LoadString (hInstance, (UINT)upResID, (TCHAR*)memBuf.Alloc (npSize * sizeof (TCHAR)), (INT)npSize);
                    ASSERT (npLen > 0);  // 前面检查过
                }
                while (npSize - npLen <= _CHAR_FUDGE);

                strRes.SetText (memBuf.GetTextPtr ());
            }
        }
    }

    return strRes;
}

HANDLE CVolAppInstance::LoadResImage (const VOL_RES_IMAGE_TYPE enImageType, const UINT_P upResID)
{
    ASSERT (enImageType >= 0 && enImageType < _NUM_VOL_RES_IMAGE_TYPES);

#ifdef _VOL_FOR_UI_DESIGNER
    if (m_szResourceRedirect != NULL)  // 转向载入所指定图像文件?
    {
        ASSERT_R_STR (m_szResourceRedirect);

        HANDLE hRes = NULL;
        if (*m_szResourceRedirect != '\0')  // 不为空资源?
        {
            if (enImageType == VRIT_CURSOR || enImageType == VRIT_ICON)  // 如果为这两类图像资源,则首先查找缓冲记录中是否已经存在.
            {
                const INT_P npIndex = m_saryCachedImageFileNames.IFindFirstElement (m_szResourceRedirect);

                if (npIndex != -1)  // 已经被载入?
                {
                    if (m_naryCachedImageTypes [npIndex] != enImageType)  // 类型与所载入图像的类型不匹配?
                        return NULL;

                    return (HANDLE)m_uaryCachedImageHandles [npIndex];
                }
            }

            // 转向为载入所指定图像文件
            hRes = LoadResImageFile (enImageType, m_szResourceRedirect);

            if (hRes != NULL &&  // 载入成功?
                    // 所载入的VRIT_CURSOR和VRIT_ICON图像资源调用方不负责释放,所以必须记录下来在程序退出时统一释放.
                    // 所载入的VRIT_BITMAP和VRIT_IMAGE_LIST图像资源由调用方负责释放,所以不需记录.
                    (enImageType == VRIT_CURSOR || enImageType == VRIT_ICON))
            {
                // 记录到缓冲数组中
                m_saryCachedImageFileNames.Add (m_szResourceRedirect);
                m_uaryCachedImageHandles.Add ((UINT_P)hRes);
                m_naryCachedImageTypes.Add (enImageType);
            }
        }

        m_szResourceRedirect = NULL;  // 取消后续转向
        return hRes;
    }
    else
#endif
    {
        if (upResID != 0)  // 不为空资源?
        {
            const HMODULE hInstance = GetInstanceHandle ();

            if (enImageType == VRIT_BITMAP || enImageType == VRIT_IMAGE_LIST)
            {
                const HRSRC hSrc = FindResource (hInstance, MAKEINTRESOURCE ((WORD)upResID), RT_RCDATA);

                if (hSrc != NULL)
                {
                    HBITMAP hBitmap = NULL;

                    const HGLOBAL hResData = LoadResource (hInstance, hSrc);
                    if (hResData != NULL)
                    {
                        const BYTE* pb = (const BYTE*)LockResource (hResData);
                        if (pb != NULL)
                        {
                            CVolImage objImage;
                            if (objImage.LoadFromMemory (pb, (INT_P)SizeofResource (hInstance, hSrc)))
                                hBitmap = objImage.Detach ();

                            UnlockResource (hResData);
                        }

                        FreeResource (hResData);
                    }

                    if (hBitmap != NULL)
                    {
                        if (enImageType == VRIT_IMAGE_LIST)
                        {
                            const HIMAGELIST hImageList = sCreateImageListFromBitmap (hBitmap);
                            ::DeleteObject (hBitmap);
                            return hImageList;
                        }

                        return hBitmap;
                    }
                }
            }
            else
            {
                switch (enImageType)
                {
                case VRIT_CURSOR:
                    return (HANDLE)::LoadCursor (hInstance, MAKEINTRESOURCE (upResID));

                case VRIT_ICON:
                    return (HANDLE)::LoadIcon (hInstance, MAKEINTRESOURCE (upResID));

                /* case VRIT_BITMAP:
                     return (HANDLE)::LoadBitmap (hInstance, MAKEINTRESOURCE (upResID));

                case VRIT_IMAGE_LIST:  {
                    const HBITMAP hBitmap = ::LoadBitmap (hInstance, MAKEINTRESOURCE (upResID));
                    if (hBitmap != NULL)
                    {
                        const HIMAGELIST hImageList = sCreateImageListFromBitmap (hBitmap);
                        ::DeleteObject (hBitmap);
                        return hImageList;
                    }
                    break; } */
                }
            }
        }

        return NULL;
    }
}

HBITMAP CVolAppInstance::LoadBitmapFromMemory (const BYTE* pBitmapData, const INT_P npBitmapDataSize)
{
    CVolImage objImage;
    return (objImage.LoadFromMemory (pBitmapData, npBitmapDataSize) ? objImage.Detach () : NULL);
}

BOOL_P CVolAppInstance::LoadResData (const UINT_P upResID, CVolMem& memRes, const TCHAR* szResType)
{
    memRes.Empty ();

#ifdef _VOL_FOR_UI_DESIGNER
    if (m_szResourceRedirect != NULL)  // 转向载入所指定图像文件?
    {
        ASSERT_R_STR (m_szResourceRedirect);

        BOOL_P blpSucceeded;
        if (*m_szResourceRedirect != '\0')  // 不为空资源?
            blpSucceeded = (memRes.ReadFromFile (m_szResourceRedirect) >= 0);
        else
            blpSucceeded = TRUE;

        m_szResourceRedirect = NULL;  // 取消后续转向
        return blpSucceeded;
    }
#endif

    //-------------------------------------------------------------------------------

    if (upResID == 0)  // 为空资源?
        return TRUE;  // 返回载入成功

    BOOL_P blpLoadSucceeded = FALSE;

    do
    {
        const HMODULE hModule = GetInstanceHandle ();
        const HRSRC hSrc = FindResource (hModule, MAKEINTRESOURCE ((WORD)upResID), szResType);
        if (hSrc == NULL)
            break;

        const HGLOBAL hResData = LoadResource (hModule, hSrc);
        if (hResData == NULL)
            break;

        const BYTE* pb = (const BYTE*)LockResource (hResData);
        if (pb != NULL)
        {
            memRes.CopyFrom (pb, (INT_P)SizeofResource (hModule, hSrc));
            blpLoadSucceeded = TRUE;

            UnlockResource (hResData);
        }

        FreeResource (hResData);
    }
    while (FALSE);

    return blpLoadSucceeded;
}

BOOL_P CVolAppInstance::LoadResData (const UINT_P upResID, CVolString& strRes)
{
    strRes.Empty ();

    CVolMem memRes;
    if (LoadResData (upResID, memRes) == FALSE)
        return FALSE;

    memRes.AddDWord (0);  // 加入结束零

    const WORD* pw = memRes.GetWordPtr ();
    if (*pw == 0xFEFF)  // 为MS的unicode文本文件起始标志?
        pw++;  // 将其跳过

    strRes.SetText ((const TCHAR*)pw);
    return TRUE;
}

//----------------------------------------------------------------------------------------------

void* CVolCommonBase::operator new (size_t size)
{
    return g_objVolApp.GetPoolMem ()->Alloc (size);
}

void* CVolCommonBase::operator new[] (size_t size)
{
    return g_objVolApp.GetPoolMem ()->Alloc (size);
}

void CVolCommonBase::operator delete (void* p)
{
    g_objVolApp.GetPoolMem ()->Free (p);
}

void CVolCommonBase::operator delete[] (void* p)
{
    g_objVolApp.GetPoolMem ()->Free (p);
}

void* CVolCommonBase::operator new (size_t, void* p)
{
    return p;
}

//----------------------------------------------------------------------------------------------

void* CVolCommonBaseWithMemManager::mgrAlloc (const INT_P npSize) const
{
    return g_objVolApp.GetPoolMem ()->Alloc (npSize);
}

void* CVolCommonBaseWithMemManager::mgrAllocMaybeRetNull (const INT_P npSize)
{
    return g_objVolApp.GetPoolMem ()->AllocMaybeRetNull (npSize);
}

void* CVolCommonBaseWithMemManager::mgrRealloc (const void* p, const INT_P npNewSize) const
{
    return g_objVolApp.GetPoolMem ()->Realloc (p, npNewSize);
}

void CVolCommonBaseWithMemManager::mgrFree (const void* p) const
{
    if (p != NULL)
        g_objVolApp.GetPoolMem ()->Free (p);
}

void* CVolCommonBaseWithMemManager::GetMemManager () const
{
    return g_objVolApp.GetPoolMem ();
}

//----------------------------------------------------------------------------------------------

void CVolException::_CopySelfFrom (const CVolException& objCopyFrom)
{
    m_nCode = objCopyFrom.m_nCode;
    m_strDesc.SetText (objCopyFrom.m_strDesc);
}

BOOL CVolException::_IsSelfEqual (const CVolException& objCompare) const
{
    return (m_nCode == objCompare.m_nCode);
}

//----------------------------------------------------------------------------------------------

CVolEventReceiver::CVolEventReceiver ()
{
    m_fnReceiver = NULL;
    m_pEventReceiver = NULL;
    m_nTagNumber = 0;
}

void CVolEventReceiver::SetReceiver (VOID_FUNC fnReceiver, CVolEventObjectPointer* pEventReceiver, INT nTagNumber)
{
    CVolEventObjectPointer* pReleaseEventReceiver;

    if (pEventReceiver == NULL)  // 删除已经置入的事件接收器?
    {
        m_locker.lock ();

        m_fnReceiver = NULL;
        m_nTagNumber = 0;

        pReleaseEventReceiver = m_pEventReceiver;
        m_pEventReceiver = NULL;

        m_locker.unlock ();
    }
    else
    {
        ASSERT (fnReceiver != NULL);

        m_locker.lock ();

        m_fnReceiver = fnReceiver;
        m_nTagNumber = nTagNumber;

        if (m_pEventReceiver == pEventReceiver)
        {
            m_locker.unlock ();
            return;
        }

        pReleaseEventReceiver = m_pEventReceiver;
        m_pEventReceiver = pEventReceiver;

        pEventReceiver->AddRef ();
        m_locker.unlock ();
    }

    if (pReleaseEventReceiver != NULL)
        pReleaseEventReceiver->Release ();
}

CVolEventObjectPointer* CVolEventReceiver::BeginSendEvent (VOID_FUNC* pfnReceiver, INT* pnTagNumber)
{
    ASSERT (pfnReceiver != NULL && pnTagNumber != NULL);

    m_locker.lock ();

    *pfnReceiver = m_fnReceiver;
    *pnTagNumber = m_nTagNumber;
    
    CVolEventObjectPointer* pEventReceiver = m_pEventReceiver;
    if (pEventReceiver != NULL)
    {
        pEventReceiver->AddRef ();
        ASSERT (m_fnReceiver != NULL);
    }

    m_locker.unlock ();

    if (pEventReceiver == NULL)
        return NULL;

    return (pEventReceiver->BeginSendEvent () ? pEventReceiver : NULL);
}

void CVolEventReceiver::sEndSendEvent (CVolEventObjectPointer* pEventReceiver)
{
    ASSERT (pEventReceiver != NULL);

    pEventReceiver->EndSendEvent ();
    pEventReceiver->Release ();
}

//----------------------------------------------------------------------------------------------

BOOL_P CVolEventObjectPointer::BeginSendEvent ()
{
    CMutexLocker locker (m_mxCounter);
    ASSERT (m_npNumSendingEvents >= 0);

    if (m_npNumSendingEvents == 0 &&  // 为第一个被发送的事件?
            m_mxEventSend.lock (TRUE) == FALSE)  // 事件已经被禁止发送(事件接收对象已经清除了对象指针记录)?
    {
        return FALSE;
    }

    m_npNumSendingEvents++;

    if (m_pVolObject != NULL)  // 存在事件接收对象?
        return TRUE;  // 返回成功

    FAIL;  // 正常情况下,如果能够成功对m_mxEventSend加锁,说明尚未调用过ReleasePointer.

    EndSendEvent ();
    return FALSE;
}

void CVolEventObjectPointer::EndSendEvent ()
{
    CMutexLocker locker (m_mxCounter);

    m_npNumSendingEvents--;
    ASSERT (m_npNumSendingEvents >= 0);

    if (m_npNumSendingEvents == 0)  // 为最后一个正在发送的事件?
        m_mxEventSend.unlock ();  // 允许事件接收对象清除对象指针记录并销毁自身
}

//----------------------------------------------------------------------------------------------

void CExternFunctionLoader::Cleanup ()
{
    const INT_P npNumLibs = m_aryLibHandles.GetCount ();

    for (INT_P npIndex = 0; npIndex < npNumLibs; npIndex++)
        MFreeLibrary ((H_LIB)m_aryLibHandles [npIndex]);

    m_aryLibHandles.RemoveAll ();
}

BOOL_P CExternFunctionLoader::InitExternFuncTable (EXTERN_FUNC_ITEM* pExternFuincTable, const BOOL_P blpThrowExceptionIfFailed)
{
    if (pExternFuincTable == NULL)
        return TRUE;

#ifdef _PF_WINDOWS
    // 获得程序当前所处目录
    CVolString strInstancePath;
    const BOOL_P blpGetInstancePathSucceeded = GetInstancePath (g_objVolApp.GetInstanceHandle (), strInstancePath);
#endif

    H_LIB hLastLib = 0;
    const TCHAR* szLastLibFileName = _T ("");

    for (; pExternFuincTable->m_szLibFileName != NULL; pExternFuincTable++)
    {
        H_LIB hLib;
        if (*pExternFuincTable->m_szLibFileName == '\0')  // 使用上一项的库文件?
        {
            ASSERT (IsEmptyStr (szLastLibFileName) == FALSE);  // 正常表应该不会出现此数据
            hLib = hLastLib;
        }
        else
        {
        #ifdef _PF_WINDOWS
            const TCHAR* szLibFileName = pExternFuincTable->m_szLibFileName;

            // 如果为相对路径,则将其转换为绝对路径.
            CVolMem memBuf;
            if (blpGetInstancePathSucceeded)  // 前面获取程序当前所处目录成功?
                szLibFileName = LinkOSPath (strInstancePath.GetText (), szLibFileName, memBuf, OS_PATH_CHAR);

            hLib = MLoadLibrary (szLibFileName);  // 载入该动态链接库

            // 如果载入失败则直接去程序当前所处目录去尝试载入
            if (hLib == 0 &&
                    blpGetInstancePathSucceeded &&
                    _tcschr (pExternFuincTable->m_szLibFileName, OS_PATH_CHAR) != NULL)  // 文件名中存在路径部分?
            {
                hLib = MLoadLibrary ((strInstancePath + GetOSFileNameWithoutPath (pExternFuincTable->m_szLibFileName)).GetText ());
            }

            // 最后尝试直接载入
            if (hLib == 0 &&
                    szLibFileName != pExternFuincTable->m_szLibFileName)
            {
                hLib = MLoadLibrary (pExternFuincTable->m_szLibFileName);
            }
        #else
            hLib = MLoadLibrary (pExternFuincTable->m_szLibFileName);  // 载入该动态链接库
        #endif

            if (hLib != 0)
                m_aryLibHandles.Add ((UINT_P)hLib);  // 记录下来用作退出时释放

            szLastLibFileName = pExternFuincTable->m_szLibFileName;
            hLastLib = hLib;
        }

        if (hLib == 0)  // 载入外部库失败?
        {
            if (blpThrowExceptionIfFailed)
            {
                CVolString str;
                str.Format (_T_LOAD_EXTERN_DLL_FAILED_S, szLastLibFileName);
                throw CVolException (VE_INIT_EXTERN_FUNC_TABLE_FAILED, str.GetText ());
            }

            return FALSE;
        }

        ASSERT (IsEmptyStr (pExternFuincTable->m_szFuncName) == FALSE);
        pExternFuincTable->m_func = MGetProcAddress (hLib,
                (*pExternFuincTable->m_szFuncName == '@' ?  // 为输入序号?
                    (U8CHAR*)atoi (pExternFuincTable->m_szFuncName + 1) :
                    pExternFuincTable->m_szFuncName));

        if (pExternFuincTable->m_func == NULL)  // 查找所指定名称函数失败?
        {
            if (blpThrowExceptionIfFailed)
            {
                CVolString str;
                str.Format (_T_NOT_FOUND_EXTERN_FUNCTION_SS,
                        szLastLibFileName, CVolString (pExternFuincTable->m_szFuncName).GetText ());
                throw CVolException (VE_INIT_EXTERN_FUNC_TABLE_FAILED, str.GetText ());
            }

            return FALSE;
        }
    }

    return TRUE;
}

//----------------------------------------------------------------------------------------------

CVolComDllLoader::CVolComDllLoader (const TCHAR* szDllFileName, const VOL_CLASS_SIGNATURE_INFO_WITH_NAME* pVolSysClassSignInfo) :
        m_szDllFileName (szDllFileName),
        m_pVolSysClassSignInfo (pVolSysClassSignInfo)
{
    ASSERT (IsEmptyStr (szDllFileName) == FALSE);

    m_hLib = 0;
    m_pFuncTable = NULL;
}

void CVolComDllLoader::Cleanup ()
{
    CMutexLocker locker (m_mxGetFunc);

    if (m_hLib != 0)
    {
        MFreeLibrary (m_hLib);
        m_hLib = 0;
    }

    m_pFuncTable = NULL;
}

VOL_COM_DLL_FUNC CVolComDllLoader::GetFunc (const INT_P npFuncIndex)
{
    ASSERT (npFuncIndex >= -1);

    if (npFuncIndex == -1)  // 清理本载入器?
    {
        Cleanup ();
        return NULL;
    }

    CMutexLocker locker (m_mxGetFunc);

    if (m_pFuncTable == NULL)  // 尚未载入?
    {
        ASSERT (m_hLib == 0);

    #ifdef _PF_WINDOWS
        const TCHAR* szDllFileName = m_szDllFileName;

        // 获得程序当前所处目录
        CVolString strInstancePath;
        const BOOL_P blpGetInstancePathSucceeded = GetInstancePath (g_objVolApp.GetInstanceHandle (), strInstancePath);

        // 如果为相对路径,则将其转换为绝对路径.
        CVolMem memBuf;
        if (blpGetInstancePathSucceeded)  // 前面获取程序当前所处目录成功?
            szDllFileName = LinkOSPath (strInstancePath.GetText (), szDllFileName, memBuf, OS_PATH_CHAR);

        m_hLib = MLoadLibrary (szDllFileName);  // 载入该动态链接库

        // 如果载入失败则直接去程序当前所处目录去尝试载入
        if (m_hLib == 0 &&
                blpGetInstancePathSucceeded &&
                _tcschr (m_szDllFileName, OS_PATH_CHAR) != NULL)  // 文件名中存在路径部分?
        {
            m_hLib = MLoadLibrary ((strInstancePath + GetOSFileNameWithoutPath (m_szDllFileName)).GetText ());
        }

        // 最后尝试直接载入
        if (m_hLib == 0 && szDllFileName != m_szDllFileName)
            m_hLib = MLoadLibrary (m_szDllFileName);
    #else
        m_hLib = MLoadLibrary (m_szDllFileName);  // 载入该动态链接库
    #endif

        const VOL_CLASS_SIGNATURE_INFO* pVolSysClassSignInfo = NULL;
        if (m_hLib != 0)  // 部件DLL载入成功?
        {
            FN_GET_VOL_COM_INFO fnGetter = (FN_GET_VOL_COM_INFO)MGetProcAddress (m_hLib, _AT_VOL_COM_INFO_GETTER_NAME);
            if (fnGetter != NULL)
                m_pFuncTable = fnGetter (&pVolSysClassSignInfo);
        }

        CVolString strErrorMessage;
        if (m_pFuncTable == NULL)  // 前面载入失败?
        {
            strErrorMessage.Format ((m_hLib == 0 ? _T_LOAD_VOL_COM_DLL_FAILED_S : _T_GET_VOL_COM_DLL_FUNC_TABLE_FAILED_S), m_szDllFileName);
        }
        else
        {
            if (pVolSysClassSignInfo != NULL && m_pVolSysClassSignInfo != NULL)
            {
                // 检查类签名信息
                CMVoidPtrArray aryNotMatchSysClassSignInfos;
                const INT_P npNumNotMatchInfos = CheckSysClassSignInfo (pVolSysClassSignInfo, m_pVolSysClassSignInfo, aryNotMatchSysClassSignInfos);

                if (npNumNotMatchInfos > 0)
                {
                    strErrorMessage.Format (_T_FOUND_NOT_MATCH_SYS_CLASSES_S, m_szDllFileName);

                #ifdef _DEBUG
                    // 非调试版的 VOL_CLASS_SIGNATURE_INFO_WITH_NAME.m_szClassFullName 成员为空文本,因此无需显示.
                    for (INT_P npIndex = 0; npIndex < npNumNotMatchInfos; npIndex++)
                    {
                        if (npIndex > 0)
                            strErrorMessage.AddText (_T (", "));
                        strErrorMessage.AddText (((const VOL_CLASS_SIGNATURE_INFO_WITH_NAME*)aryNotMatchSysClassSignInfos [npIndex])->m_szClassFullName);
                    }
                #endif
                }
            }
        }

        if (strErrorMessage.IsEmpty () == FALSE)
        {
            TRACE0 (strErrorMessage.GetText ());
        #ifdef _PF_WINDOWS
            HWND hParentWnd = ::GetActiveWindow ();
            if (hParentWnd == NULL)
                hParentWnd = ::GetDesktopWindow ();
            ::MessageBox (hParentWnd, strErrorMessage.GetText (), _T_FATAL_RUNTIME_ERROR_CAPTION, (MB_OK | MB_ICONERROR));
            DebugBreak ();
            ExitProcess (-1);  // 载入失败则退出程序
        #else
            exit (-1);  
        #endif

            return NULL;
        }
    }

    return m_pFuncTable [npFuncIndex];
}

INT_P CVolComDllLoader::CheckSysClassSignInfo (const VOL_CLASS_SIGNATURE_INFO* pVolSysClassSignInfo1,
        const VOL_CLASS_SIGNATURE_INFO_WITH_NAME* pVolSysClassSignInfo2, CMVoidPtrArray& aryNotMatchSysClassSignInfos) const
{
    ASSERT (pVolSysClassSignInfo1 != NULL && pVolSysClassSignInfo2 != NULL);  // 进入本方法的前提

    aryNotMatchSysClassSignInfos.RemoveAll ();

    for (; pVolSysClassSignInfo1->m_upClassSize > 0 && pVolSysClassSignInfo2->m_infSign.m_upClassSize > 0;
            pVolSysClassSignInfo1++, pVolSysClassSignInfo2++)
    {
        if (pVolSysClassSignInfo1->m_upClassSize != pVolSysClassSignInfo2->m_infSign.m_upClassSize)  // 当前类签名检查失败
            aryNotMatchSysClassSignInfos.Add ((void*)pVolSysClassSignInfo2);
    }

    return aryNotMatchSysClassSignInfos.GetCount ();
}

//----------------------------------------------------------------------------------------------

#define _VOL_SEND_NOTICE_MSG  (WM_APP + 1)
#define _VOL_POST_NOTICE_MSG  (WM_APP + 2)
#define _VOL_NOTICE_ACK_CODE  18
#define _T_VOL_NORMAL_NOTICE_RECEIVER_WINDOW_CLASS_NAME _T ("_VOL_IVolNoticeReceiver")

typedef struct
{
    INT_P m_npCode, m_npParam1, m_npParam2;
    INT_P* m_pnpResult;
}
_VOL_NOTICE_INFO;

IVolNoticeReceiver::~IVolNoticeReceiver ()
{
    if (m_hWnd != NULL)
    {
        ::RemoveProp (m_hWnd, _T_VOL_NORMAL_NOTICE_RECEIVER_WINDOW_CLASS_NAME);
        ::DestroyWindow (m_hWnd);
    }
}

LRESULT CALLBACK IVolNoticeReceiver::sVolNoticeRevWindowProc (HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    if (uMsg == _VOL_SEND_NOTICE_MSG)
    {
        if (wParam != NULL && lParam == _VOL_NOTICE_ACK_CODE)
        {
            IVolNoticeReceiver* pThis = (IVolNoticeReceiver*)::GetProp (hWnd, _T_VOL_NORMAL_NOTICE_RECEIVER_WINDOW_CLASS_NAME);

            if (pThis != NULL)
            {
                _VOL_NOTICE_INFO* pInf = (_VOL_NOTICE_INFO*)wParam;
                const INT_P npResult = pThis->OnNotify (pInf->m_npCode, pInf->m_npParam1, pInf->m_npParam2);

                if (pInf->m_pnpResult != NULL)
                    *pInf->m_pnpResult = npResult;

                return _VOL_NOTICE_ACK_CODE;
            }
        }
    }
    else if (uMsg == _VOL_POST_NOTICE_MSG)
    {
        IVolNoticeReceiver* pThis = (IVolNoticeReceiver*)::GetProp (hWnd, _T_VOL_NORMAL_NOTICE_RECEIVER_WINDOW_CLASS_NAME);

        if (pThis != NULL)
            pThis->OnNotify (wParam, lParam, 0);
    }
    else if (uMsg == WM_NCDESTROY)
    {
        ::RemoveProp (hWnd, _T_VOL_NORMAL_NOTICE_RECEIVER_WINDOW_CLASS_NAME);
    }

    return ::DefWindowProc (hWnd, uMsg, wParam, lParam);
}

BOOL_P IVolNoticeReceiver::InitReceiver ()
{
    if (m_hWnd == NULL)
    {
        m_hWnd = g_objVolApp.CreateHiddenWindow (_T_VOL_NORMAL_NOTICE_RECEIVER_WINDOW_CLASS_NAME, (WNDPROC)sVolNoticeRevWindowProc, NULL);

        if (m_hWnd != NULL && ::SetProp (m_hWnd, _T_VOL_NORMAL_NOTICE_RECEIVER_WINDOW_CLASS_NAME, (HANDLE)this) == FALSE)
        {
            ::DestroyWindow (m_hWnd);
            m_hWnd = NULL;
        }
    }

    return (m_hWnd != NULL);
}

BOOL_P IVolNoticeReceiver::Notify (INT_P npCode, INT_P npParam1, INT_P npParam2, INT_P* pnpResult)
{
    if (pnpResult != NULL)
        *pnpResult = 0;

    if (m_hWnd != NULL)
    {
        _VOL_NOTICE_INFO inf;
        inf.m_pnpResult = pnpResult;
        inf.m_npCode = npCode;
        inf.m_npParam1 = npParam1;
        inf.m_npParam2 = npParam2;

        if (::SendMessage (m_hWnd, _VOL_SEND_NOTICE_MSG, (WPARAM)&inf, _VOL_NOTICE_ACK_CODE) == _VOL_NOTICE_ACK_CODE)
            return TRUE;
    }

    return FALSE;
}

void IVolNoticeReceiver::Post (INT_P npCode, INT_P npParam1)
{
    if (m_hWnd != NULL)
        ::PostMessage (m_hWnd, _VOL_POST_NOTICE_MSG, (WPARAM)npCode, (LPARAM)npParam1);
}

//----------------------------------------------------------------------------------------------

#define _VANR_TIMER_ID  1  // 时钟ID
#define _VANR_TIMER_CHECK_INTERVAL  300  // 时钟检查周期时间
#define _T_VOL_ADV_NOTICE_RECEIVER_WINDOW_CLASS_NAME _T ("_VOL_IVolAdvNoticeReceiver")

// 记录将被发送的通知信息
typedef struct
{
    INT_P m_npCode, m_npParam1, m_npParam2;
    CRefObject* m_pParamObject;  // 记录参数对象,为NULL表示无.

    INT_P* m_pnpResult;
}
_VOL_ADV_SENDED_NOTICE;

// 记录将被投递的通知信息
typedef struct
{
    INT_P m_npCode, m_npParam1, m_npParam2;
    CRefObject* m_pParamObject;  // 记录参数对象,为NULL表示无.

    DWORD m_dwNotifyTime;  // 记录本被投递通知的记录时间
    UINT_P m_upNoticeNumber;  // 记录本被投递通知的投递编号,必定不为0.
}
_VOL_ADV_POSTED_NOTICE;

IVolAdvNoticeReceiver::IVolAdvNoticeReceiver ()
{
    m_hWnd = NULL;
    m_upFreeNoticeNumber = 0;
    SetMaxPostedNoticeKeepTime (1000);

    m_memPostedNotices.SetMemAlignSize (sizeof (_VOL_ADV_POSTED_NOTICE) * 64);
    InitReceiver ();
}

BOOL_P IVolAdvNoticeReceiver::InitReceiver ()
{
    if (m_hWnd == NULL)
    {
        m_hWnd = g_objVolApp.CreateHiddenWindow (_T_VOL_ADV_NOTICE_RECEIVER_WINDOW_CLASS_NAME, (WNDPROC)sVolAdvNoticeRevWindowProc, NULL);

        if (m_hWnd != NULL &&
                (::SetProp (m_hWnd, _T_VOL_ADV_NOTICE_RECEIVER_WINDOW_CLASS_NAME, (HANDLE)this) == FALSE ||
                    ::SetTimer (m_hWnd, _VANR_TIMER_ID, _VANR_TIMER_CHECK_INTERVAL, NULL) == 0))  // 用作定时释放所有超时的被投递通知
        {
            ::DestroyWindow (m_hWnd);
            m_hWnd = NULL;
        }
    }

    return (m_hWnd != NULL);
}

IVolAdvNoticeReceiver::~IVolAdvNoticeReceiver ()
{
    if (m_hWnd != NULL)
    {
        ::RemoveProp (m_hWnd, _T_VOL_ADV_NOTICE_RECEIVER_WINDOW_CLASS_NAME);
        ::DestroyWindow (m_hWnd);
    }

    CMutexLocker locker (m_mxLocker);

    // 清除所有尚未被投递的通知
    const INT_P npCount = m_memPostedNotices.GetNumUserObjects (sizeof (_VOL_ADV_POSTED_NOTICE));
    _VOL_ADV_POSTED_NOTICE* pNotice = (_VOL_ADV_POSTED_NOTICE*)m_memPostedNotices.GetPtr ();

    for (INT_P npIndex = 0; npIndex < npCount; npIndex++, pNotice++)
        pNotice->m_pParamObject->SafeRelease ();
    ASSERT (m_memPostedNotices.IsAtEnd (pNotice));
}

void IVolAdvNoticeReceiver::SetMaxPostedNoticeKeepTime (INT nMaxPostedNoticeKeepTime)
{
    m_dwMaxPostedNoticeKeepTime = (DWORD)MAX (0, nMaxPostedNoticeKeepTime);

    // 用作确保前面的时钟事件不会销毁掉后面刚投递的消息
    if (m_dwMaxPostedNoticeKeepTime != 0 && m_dwMaxPostedNoticeKeepTime < 20)
        m_dwMaxPostedNoticeKeepTime = 20;
}

void IVolAdvNoticeReceiver::ProcessPostedNotice (const UINT_P upNoticeNumber)
{
    ASSERT (upNoticeNumber != 0);

    m_mxLocker.lock ();

    const INT_P npCount = m_memPostedNotices.GetNumUserObjects (sizeof (_VOL_ADV_POSTED_NOTICE));
    const _VOL_ADV_POSTED_NOTICE* pNotice = (_VOL_ADV_POSTED_NOTICE*)m_memPostedNotices.GetPtr ();

    // 查找对应的通知信息(有可能因为已经超时被销毁),如果找到则将其发送.
    for (INT_P npIndex = 0; npIndex < npCount; npIndex++, pNotice++)
    {
        if (pNotice->m_upNoticeNumber == upNoticeNumber)  // 找到了对应编号的通知?
        {
            _VOL_ADV_POSTED_NOTICE inf;
            COPY_MEM (&inf, pNotice, sizeof (_VOL_ADV_POSTED_NOTICE));
            m_memPostedNotices.Remove (npIndex * sizeof (_VOL_ADV_POSTED_NOTICE), sizeof (_VOL_ADV_POSTED_NOTICE));
            m_mxLocker.unlock ();

            OnNotify (inf.m_npCode, inf.m_npParam1, inf.m_npParam2, inf.m_pParamObject);  // 将其发送
            inf.m_pParamObject->SafeRelease ();  // 发送完毕即可删除对应的对象

            return;
        }
    }

    m_mxLocker.unlock ();
}

void IVolAdvNoticeReceiver::CheckFreeTimeoutNotices ()
{
    if (m_dwMaxPostedNoticeKeepTime == 0)  // 不需要定时清除已经超时的被投递通知?
        return;

    const DWORD dwCurrentTime = ::GetTickCount ();  // 获得当前时间
    CMutexLocker locker (m_mxLocker);

    // 清除所有过期的被投递消息参数
    const INT_P npCount = m_memPostedNotices.GetNumUserObjects (sizeof (_VOL_ADV_POSTED_NOTICE));
    for (INT_P npIndex = npCount - 1; npIndex >= 0; npIndex--)
    {
        _VOL_ADV_POSTED_NOTICE* pNotice = (_VOL_ADV_POSTED_NOTICE*)m_memPostedNotices.GetPtr () + npIndex;

        if (pNotice->m_dwNotifyTime > dwCurrentTime)  // 处理时间溢出
        {
            pNotice->m_dwNotifyTime = dwCurrentTime;
        }
        else if (pNotice->m_dwNotifyTime + m_dwMaxPostedNoticeKeepTime < dwCurrentTime)  // 已经超时?
        {
            // 将其释放
            pNotice->m_pParamObject->SafeRelease ();
            m_memPostedNotices.Remove (npIndex * sizeof (_VOL_ADV_POSTED_NOTICE), sizeof (_VOL_ADV_POSTED_NOTICE));
        }
    }
}

LRESULT CALLBACK IVolAdvNoticeReceiver::sVolAdvNoticeRevWindowProc (HWND hWnd, UINT uMsg, WPARAM wParam, LPARAM lParam)
{
    switch (uMsg)
    {
    case _VOL_SEND_NOTICE_MSG:  // 接收到所发送过来的通知?
        if (wParam != NULL && lParam == _VOL_NOTICE_ACK_CODE)  // wParam为_VOL_ADV_SENDED_NOTICE指针
        {
            IVolAdvNoticeReceiver* pThis = (IVolAdvNoticeReceiver*)::GetProp (hWnd, _T_VOL_ADV_NOTICE_RECEIVER_WINDOW_CLASS_NAME);

            if (pThis != NULL)
            {
                _VOL_ADV_SENDED_NOTICE* pInf = (_VOL_ADV_SENDED_NOTICE*)wParam;
                const INT_P npResult = pThis->OnNotify (pInf->m_npCode, pInf->m_npParam1, pInf->m_npParam2, pInf->m_pParamObject);

                if (pInf->m_pnpResult != NULL)  // 需要返回值?
                    *pInf->m_pnpResult = npResult;

                return _VOL_NOTICE_ACK_CODE;
            }
        }
        break;

    case _VOL_POST_NOTICE_MSG:  // 接收到所投递过来的通知?
        if (wParam != 0 && lParam == _VOL_NOTICE_ACK_CODE)  // wParam为通知编号(非0)
        {
            IVolAdvNoticeReceiver* pThis = (IVolAdvNoticeReceiver*)::GetProp (hWnd, _T_VOL_ADV_NOTICE_RECEIVER_WINDOW_CLASS_NAME);

            if (pThis != NULL)
                pThis->ProcessPostedNotice ((UINT_P)wParam);
        }
        break;

    case WM_TIMER:  {
        IVolAdvNoticeReceiver* pThis = (IVolAdvNoticeReceiver*)::GetProp (hWnd, _T_VOL_ADV_NOTICE_RECEIVER_WINDOW_CLASS_NAME);
        if (pThis != NULL)
            pThis->CheckFreeTimeoutNotices ();
        break;  }

    case WM_NCDESTROY:
        ::RemoveProp (hWnd, _T_VOL_ADV_NOTICE_RECEIVER_WINDOW_CLASS_NAME);
        break;
    }

    return ::DefWindowProc (hWnd, uMsg, wParam, lParam);
}

BOOL_P IVolAdvNoticeReceiver::SendNotice (INT_P npCode, INT_P npParam1, INT_P npParam2, CRefObject* pParamObject, INT_P* pnpResult)
{
    if (pnpResult != NULL)
        *pnpResult = 0;

    if (m_hWnd != NULL)
    {
        _VOL_ADV_SENDED_NOTICE inf;
        inf.m_pnpResult = pnpResult;
        inf.m_npCode = npCode;
        inf.m_npParam1 = npParam1;
        inf.m_npParam2 = npParam2;
        inf.m_pParamObject = pParamObject;

        if (::SendMessage (m_hWnd, _VOL_SEND_NOTICE_MSG, (WPARAM)&inf, _VOL_NOTICE_ACK_CODE) == _VOL_NOTICE_ACK_CODE)
            return TRUE;
    }

    return FALSE;
}

void IVolAdvNoticeReceiver::PostNotice (INT_P npCode, INT_P npParam1, INT_P npParam2, CRefObject* pParamObject)
{
    if (m_hWnd == NULL)
        return;

    _VOL_ADV_POSTED_NOTICE inf;
    inf.m_npCode = npCode;
    inf.m_npParam1 = npParam1;
    inf.m_npParam2 = npParam2;
    inf.m_dwNotifyTime = ::GetTickCount ();  // 记录投递时间

    inf.m_pParamObject = pParamObject;
    if (pParamObject != NULL)
        pParamObject->AddRef ();

    // 记录消息编号
    m_upFreeNoticeNumber++;
    if (m_upFreeNoticeNumber == 0)
        m_upFreeNoticeNumber++;
    inf.m_upNoticeNumber = m_upFreeNoticeNumber;

    m_mxLocker.lock ();
    m_memPostedNotices.Append (&inf, sizeof (inf));  // 压入缓存池中
    m_mxLocker.unlock ();

    ::PostMessage (m_hWnd, _VOL_POST_NOTICE_MSG, (WPARAM)m_upFreeNoticeNumber, _VOL_NOTICE_ACK_CODE);  // 将其投递
}

//----------------------------------------------------------------------------------------------

void CWindowTimeTrigger::Reset (const DWORD dwTriggerInterval)
{
    m_dwTriggerInterval = dwTriggerInterval;
    m_dwNextTriggerTime = 0;  // 用作确保重置后立即触发一次
}

BOOL_P CWindowTimeTrigger::OnTimeAdvance ()
{
    if (m_dwTriggerInterval == 0)  // 触发器被停止?
        return FALSE;  // 返回未被触发

    const DWORD dwCurrentTime = GetTickCount ();
    if (dwCurrentTime >= m_dwNextTriggerTime)  // 到了触发时间?
    {
        m_dwNextTriggerTime = dwCurrentTime + m_dwTriggerInterval;  // 更新下一次的触发时间
        return TRUE;  // 返回被触发
    }

    return FALSE;  // 返回未被触发
}

void CWindowTimeTrigger::SetNextTriggerInterval (const DWORD dwNextTriggerInterval)
{
    m_dwNextTriggerTime = GetTickCount () + dwNextTriggerInterval;
}

//----------------------------------------------------------------------------------------------

void CVolWindowProcFilters::Cleanup ()
{
    VOL_WIN_PROC_FILTER_INFO* pInf = m_pinfFirstFilter;
    while (pInf != NULL)
    {
        VOL_WIN_PROC_FILTER_INFO* pinfNextFilter = pInf->m_pinfNextFilter;
        delete pInf;
        pInf = pinfNextFilter;
    }

    m_pinfFirstFilter = NULL;
}

void CVolWindowProcFilters::RegisterFilter (IVolWindowProcFilter* pMsgFilter)
{
    ASSERT (pMsgFilter != NULL);

    // 首先检查是否已经存在
    VOL_WIN_PROC_FILTER_INFO* pInf = m_pinfFirstFilter;
    while (pInf != NULL)
    {
        if (pInf->m_pMsgFilter == pMsgFilter)
            return;
        pInf = pInf->m_pinfNextFilter;
    }

    pInf = new VOL_WIN_PROC_FILTER_INFO;
    pInf->m_pMsgFilter = pMsgFilter;
    pInf->m_pinfNextFilter = m_pinfFirstFilter;

    m_pinfFirstFilter = pInf;
}

BOOL_P CVolWindowProcFilters::UnregisterFilter (IVolWindowProcFilter* pMsgFilter)
{
    if (pMsgFilter == NULL)
    {
        Cleanup ();
        return TRUE;
    }

    VOL_WIN_PROC_FILTER_INFO* pPrevInf = NULL;
    VOL_WIN_PROC_FILTER_INFO* pInf = m_pinfFirstFilter;

    while (pInf != NULL)
    {
        if (pInf->m_pMsgFilter == pMsgFilter)
        {
            if (pPrevInf == NULL)
            {
                ASSERT (pInf == m_pinfFirstFilter);
                m_pinfFirstFilter = pInf->m_pinfNextFilter;
            }
            else
            {
                pPrevInf->m_pinfNextFilter = pInf->m_pinfNextFilter;
            }

            delete pInf;
            return TRUE;
        }

        pPrevInf = pInf;
        pInf = pInf->m_pinfNextFilter;
    }

    return FALSE;
}

BOOL_P CVolWindowProcFilters::CallFilterBeforeDefProc (HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam, LRESULT& lResult)
{
    if (hWnd != NULL)
    {
        VOL_WIN_PROC_FILTER_INFO* pInf = m_pinfFirstFilter;
        while (pInf != NULL)
        {
            ASSERT (pInf->m_pMsgFilter != NULL);

            VOL_WIN_PROC_FILTER_INFO* pNextInf = pInf->m_pinfNextFilter;  // 有可能在FilterBeforeDefProc中调用UnregisterFilter删除自身
            if (pInf->m_pMsgFilter->FilterBeforeDefProc (hWnd, message, wParam, lParam, lResult))
                return TRUE;

            pInf = pNextInf;
        }
    }

    return FALSE;
}

/* BOOL_P CVolWindowProcFilters::CallFilterAfterDefProc (HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam, LRESULT& lResult)
{
    if (hWnd != NULL)
    {
        VOL_WIN_PROC_FILTER_INFO* pInf = m_pinfFirstFilter;
        while (pInf != NULL)
        {
            ASSERT (pInf->m_pMsgFilter != NULL);

            VOL_WIN_PROC_FILTER_INFO* pNextInf = pInf->m_pinfNextFilter;  // 有可能在FilterBeforeDefProc中调用UnregisterFilter删除自身
            if (pInf->m_pMsgFilter->FilterAfterDefProc (hWnd, message, wParam, lParam, lResult))
                return TRUE;

            pInf = pNextInf;
        }
    }

    return FALSE;
} */
