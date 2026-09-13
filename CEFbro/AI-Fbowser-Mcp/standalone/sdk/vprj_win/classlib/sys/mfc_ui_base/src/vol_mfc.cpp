
// Copyright (C) Recursion Company. All rights reserved.

#include "stdafx.h"
#include "vol_user_app_info.h"

IMPLEMENT_DYNAMIC (CVolMfcAppBase, CWinAppEx)

BEGIN_MESSAGE_MAP (CVolMfcAppBase, CWinAppEx)
    //{{AFX_MSG_MAP(CVolMfcAppBase)
    ON_UPDATE_COMMAND_UI (ID_FILE_MRU_FILE1, &OnUpdateRecentFileMenu)
    //}}AFX_MSG_MAP
END_MESSAGE_MAP ()

void CVolMfcAppBase::InitMdiApp (const TCHAR* szRegistryKey, BOOL blRemoveHistoryData, INT nMaxMRU)
{
    // 设置用于存储配置信息的注册表项
    if (IsEmptyStr (szRegistryKey) == FALSE)
    {
        SetRegistryKey (szRegistryKey);

        if (blRemoveHistoryData)
        {
            // 删除所有MFC历史数据
            CSettingsStoreSP regSP;
            regSP.Create (FALSE, FALSE).DeleteKey (GetRegSectionPath ());
        }
    }

    // 加载标准 INI 文件选项(包括 MRU)
    if (blRemoveHistoryData == FALSE)
        LoadStdProfileSettings ((INT)CLIP (nMaxMRU, 0, 16));

    InitContextMenuManager ();
    // InitKeyboardManager ();
    InitTooltipManager ();
    EnableTaskbarInteraction (FALSE);

    CMFCToolTipInfo ttParams;
    ttParams.m_bVislManagerTheme = TRUE;
    GetTooltipManager ()->SetTooltipParams (AFX_TOOLTIP_TYPE_ALL, RUNTIME_CLASS (CMFCToolTipCtrl), &ttParams);
}

void CVolMfcAppBase::OnUpdateRecentFileMenu (CCmdUI* pCmdUI)
{
    ASSERT (pCmdUI != NULL);

    if (m_pRecentFileList == NULL) // no MRU files
    {
        pCmdUI->Enable (FALSE);
    }
    else
    {
        CMenu* pMenu;
        if (pCmdUI->m_pSubMenu != NULL)
        {
            // 最近解决方案列表菜单项在子菜单中,而UpdateMenu中固定了对主菜单操作,此处将其中的操作转移到子菜单中.
            pMenu = pCmdUI->m_pMenu;
            pCmdUI->m_pMenu = pCmdUI->m_pSubMenu;
        }

        m_pRecentFileList->UpdateMenu (pCmdUI);

        if (pCmdUI->m_pSubMenu != NULL)
            pCmdUI->m_pMenu = pMenu;
    }
}

BOOL CVolMfcAppBase::PreTranslateMessage (MSG* pMsg)
{
    if (CWinAppEx::PreTranslateMessage (pMsg))
        return TRUE;

    return (BOOL)CVolAppInstance::sVolPreFilterInputMessage (pMsg);
}
