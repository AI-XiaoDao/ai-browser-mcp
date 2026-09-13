
// Copyright (C) Recursion Company. All rights reserved.

// 用作提供mfc头文件内容
#ifndef __VOL_MFC_H__
#define __VOL_MFC_H__

#ifdef _VOL_STATIC_RUNTIME  // 使用静态C++运行时库? 此宏由编译器建立并维护
    #ifdef _AFXDLL  // 使用MFC动态链接库?
        #error 使用MFC动态链接库时必须将项目选项中的"使用静态运行时库"同时设置为假.
    #endif
#else
    #ifndef _AFXDLL  // 使用MFC静态链接库?
        #error 使用MFC静态链接库时必须将项目选项中的"使用静态运行时库"同时设置为真.
    #endif
#endif

#define _ATL_CSTRING_EXPLICIT_CONSTRUCTORS  // 某些 CString 构造函数将是显式的
#define _AFX_ALL_WARNINGS  // 关闭 MFC 对某些常见但经常可放心忽略的警告消息的隐藏

#include <afxwin.h>  // MFC 核心组件和标准组件
#include <afxext.h>  // MFC 扩展
#include <afxdisp.h>  // MFC 自动化类

#ifndef _AFX_NO_OLE_SUPPORT
    #include <afxdtctl.h>  // MFC 对 Internet Explorer 4 公共控件的支持
#endif
#ifndef _AFX_NO_AFXCMN_SUPPORT
    #include <afxcmn.h>  // MFC 对 Windows 公共控件的支持
#endif  // _AFX_NO_AFXCMN_SUPPORT

#include <afxcontrolbars.h>  // 功能区和控件条的 MFC 支持

//----------------------------------------------------------------------

// 火山MFC程序的APP基础类
class CVolMfcAppBase : public CWinAppEx
{
    DECLARE_DYNAMIC (CVolMfcAppBase)

public:
    // 初始化MDI程序实例相关信息
    void InitMdiApp (const TCHAR* szRegistryKey, BOOL blRemoveHistoryData, INT nMaxMRU);

protected:
    virtual BOOL PreTranslateMessage (MSG* pMsg) override;

    //{{AFX_MSG(CVolMfcAppBase)
    afx_msg void OnUpdateRecentFileMenu (CCmdUI* pCmdUI);
    //}}AFX_MSG
    DECLARE_MESSAGE_MAP ()
};

#endif
