
// Copyright (C) Recursion Company. All rights reserved.

#ifndef __VOL_MENU_H__
#define __VOL_MENU_H__

// 菜单项信息
class CVolMenuItemInfo : public CVolCommonBase
{
public:
    CVolMenuItemInfo (HMENU hMenu);
    CVolMenuItemInfo (const CVolMenuItemInfo& inf);

    INT_P LoadFromMenuItemInfo (const CMStringArray& saryFields, INT_P npFieldIndex);
    static INT_P sGetMenuItemIndent (const CMStringArray& saryFields, const INT_P npFieldIndex);

protected:
    static BOOL_P sStrToBool (const TCHAR* ps, BOOL_P* pblpValue);

public:
    HMENU m_hMenu;  // 菜单项所处的菜单句柄,必定不为NULL.

    #define VOLMF_SEPARATOR  (1 << 0)  // 是否为横向分隔线
    #define VOLMF_CHECKED    (1 << 1)  // 是否被选中
    #define VOLMF_DISABLED   (1 << 2)  // 是否被禁止
    UINT_P m_upFlags;

    INT_P m_npIndent;         // 层次
    UINT_P m_upMenuItemID;    // 菜单项ID,必定不为0.
    CVolString m_strCaption;  // 标题
    CVolString m_strTip;      // 提示
    UINT_P m_upAccelKeyCode;  // 快捷键代码
    INT_P m_npImageIndex;     // 图标索引位置,为-1表示无.
};

class CRefVolMenu : public CRefObject
{
    DECLARE_DERIVED_CLASS (CRefVolMenu)

public:
    inline_ CRefVolMenu () : m_blpOwnerDraw (FALSE)
    {
        _InitMembers ();
    }

    inline_ CRefVolMenu (BOOL_P blpOwnerDraw) : m_blpOwnerDraw (blpOwnerDraw)
    {
        _InitMembers ();
    }

    virtual ~CRefVolMenu ()
    {
        Cleanup ();
    }

    void Cleanup ();  // 清理本对象的内容
    
    inline_ void _InitMembers ()
    {
        m_blpLoaded = FALSE;
        m_hMenu = NULL;
        m_hAccelTable = NULL;
    }

public:
     // 返回所生成的菜单句柄,如无则返回NULL.
    inline_ HMENU GetMenu () const
    {
        return m_hMenu;
    }
    inline_ HMENU SafeGetMenu () const
    {
        return (this == NULL ? NULL : m_hMenu);
    }

    // 返回本对象内容是否为空
    inline_ BOOL_P IsEmpty () const
    {
        return (m_hMenu == NULL);
    }

    // 返回本菜单中所生成的快捷键表,如无则返回NULL.
    inline_ HACCEL GetAccelTable () const
    {
        return m_hAccelTable;
    }
    inline_ HACCEL SafeGetAccelTable () const
    {
        return (this == NULL ? NULL : m_hAccelTable);
    }

    // 返回本菜单中的第一个子弹出菜单句柄,如不存在则返回NULL.
    inline_ HMENU SafeGetFirstSubMenu () const
    {
        return SafeGetSubMenu (0);
    }

    // 返回本菜单中的指定索引位置处子弹出菜单句柄,如不存在则返回NULL.
    inline_ HMENU SafeGetSubMenu (INT_P npSubMenuIndex) const
    {
        return ((this == NULL || m_hMenu == NULL) ? NULL : ::GetSubMenu (m_hMenu, (INT)npSubMenuIndex));
    }

    // 返回所指定的菜单项ID是否存在
    inline_ BOOL_P IsMenuItemIDExist (const UINT_P upMenuItemID) const
    {
        return (upMenuItemID != 0 && FindMenuItemInfo (upMenuItemID, NULL) != NULL);
    }

    // 从菜单设计器的设计内容文本中载入本菜单的内容,成功返回非NULL菜单句柄,失败返回NULL.
    //   szMenuDesignContent: 菜单设计器的设计内容文本,为NULL表示重载先前所记录的菜单设计内容.
    HMENU LoadFromDesignContent (const TCHAR* szMenuDesignContent, BOOL_P blpIsMDIMenu = FALSE);

    // 根据所指定消息处理本菜单中的快捷键,返回该消息是否被处理.
    BOOL_P TranslateMenuAccelerator (const HWND hWnd, const MSG* pMsg);

    // 返回所指定ID菜单项的提示文本,如无则返回空文本.
    const TCHAR* GetMenuItemTip (const UINT_P upMenuItemID) const;

    // 设置所指定ID菜单项的提示文本,返回是否成功
    BOOL_P SetMenuItemTip (const UINT_P upMenuItemID, const TCHAR* szNewTip);

    CVolString GetMenuItemCaption (UINT_P upMenuItemID);
    BOOL SetMenuItemCaption (UINT_P upMenuItemID, const TCHAR* szNewCaption);

    // 返回所指定ID菜单项的图标索引位置,如无则返回-1.
    INT GetMenuItemImageIndex (const UINT_P upMenuItemID) const;

    // 设置所指定ID菜单项的图标索引位置,返回是否成功
    BOOL_P SetMenuItemImageIndex (const UINT_P upMenuItemID, const INT_P npNewImageIndex);

    // 返回所指定ID菜单项所处菜单的句柄,如不存在则返回NULL.
    HMENU GetMenuHandle (const UINT_P upMenuItemID) const;

    // 返回本菜单中所置入的设计时内容
    inline_ const TCHAR* GetMenuDesignContent () const
    {
        return m_strMenuDesignContent.GetText ();
    }

    BOOL SetMenuItemFlags (const UINT_P upMenuItemID, UINT_P upAddFlags, UINT_P upRemoveFlags, UINT_P upInvertFlags);
    UINT_P GetMenuItemFlags (const UINT_P upMenuItemID) const;

    // 查找所指定ID菜单项的相关信息,未找到返回NULL.
    CVolMenuItemInfo* FindMenuItemInfo (UINT_P upMenuItemID, INT_P* pnpIndex) const;

    inline_ INT_P GetNumMenuItems () const
    {
        return m_arypMenuItems.GetCount ();
    }
    inline_ CVolMenuItemInfo* GetSpecMenuItemInfo (const INT_P npIndex)
    {
        return m_arypMenuItems [npIndex];
    }

    BOOL_P DeleteMenuItem (const UINT_P upMenuItemID);
    UINT_P InsertNewMenuItem (UINT_P upInsertPosMenuItemID, BOOL_P blpInsertAtTail, UINT_P upNewMenuItemID,
            const TCHAR* szNewMenuItemCaption, const TCHAR* szNewMenuItemTip, BOOL_P blpChecked, BOOL_P blpDisabled, INT_P npImageIndex);
    BOOL PopupSubMenu (INT xPos, INT yPos, BOOL_P blpIsTrayMenu, HWND hWnd, INT_P npSubMenuIndex);
    HMENU Recreate ();

    // 将本菜单与所指定的窗口绑定/解除绑定
    //   hwndBind: 提供所欲绑定的窗口句柄,绑定时不能为NULL,解除绑定时如果为NULL,表示与当前已绑定窗口进行解绑.
    //   blpBind: 为真绑定,为假解绑.
    virtual void BindWindow (HWND hwndBind, BOOL_P blpBind) {  }

protected:
    INT_P InsertPopupMenu (const HMENU hParentMenu, const CMStringArray& saryFields, INT_P npFieldIndex,
            CUIntPUniqueArray& aryupAccelKeys, CMUIntPArray& aryupAccelKeyCommandIDs, CVolMem& memSeparatorInfos);
    INT_P InsertPopupMenu (const HMENU hParentMenu, INT_P npMenuItemIndex);
    UINT_P GetFreeMenuItemID () const;

protected:
    const BOOL_P m_blpOwnerDraw; // 是否为自绘菜单

    BOOL_P m_blpLoaded;  // 记录是否已经执行了载入操作
    HMENU m_hMenu;  // 记录所生成的菜单句柄,为NULL表示无.
    HACCEL m_hAccelTable;  // 记录菜单中所生成的快捷键表,为NULL表示无.
    CVolString m_strMenuDesignContent;  // 记录菜单的设计时内容

    CMPointerArray<CVolMenuItemInfo*> m_arypMenuItems;  // 菜单项信息记录数组
};

#endif
