#pragma once
#ifndef FBROWSER_MENUMODEL_H_
#define FBROWSER_MENUMODEL_H_

class FBroString;
class FBroCefStringList;

#ifndef _FBROELIB

DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_Clear(CefRefPtr<CefMenuModel> menu);
DLLEXPORT int TEXPORTS FBroHsMenuModel_GetCount(CefRefPtr<CefMenuModel> menu);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_AddSeparator(CefRefPtr<CefMenuModel> menu);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_AddItem(CefRefPtr<CefMenuModel> menu, int command_id, const CefString& inLable);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_AddCheckItem(CefRefPtr<CefMenuModel> menu, int command_id, const CefString& inLable);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_AddRadioItem(CefRefPtr<CefMenuModel> menu, int command_id, const CefString& inLable, int group_id);
DLLEXPORT CefRefPtr<CefMenuModel> TEXPORTS FBroHsMenuModel_AddSubMenu(CefRefPtr<CefMenuModel> menu, int command_id, const CefString& inLable);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_Remove(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsMenuModel_GetLable(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetLable(CefRefPtr<CefMenuModel> menu, int command_id, const CefString& inLable);
DLLEXPORT int TEXPORTS FBroHsMenuModel_GetType(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT int TEXPORTS FBroHsMenuModel_GetGroup(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetGroup(CefRefPtr<CefMenuModel> menu, int command_id, int nGroupId);
DLLEXPORT CefRefPtr<CefMenuModel> TEXPORTS FBroHsMenuModel_GetSubMenu(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_IsVisable(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetVisable(CefRefPtr<CefMenuModel> menu, int command_id, bool visable);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_IsEnable(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetEnable(CefRefPtr<CefMenuModel> menu, int command_id, bool enable);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_IsChecked(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetCheck(CefRefPtr<CefMenuModel> menu, int command_id, bool check);

DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetCheckedAt(CefRefPtr<CefMenuModel> menu, int index, BOOL checked);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_HasAccelerator(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_HasAcceleratorAt(CefRefPtr<CefMenuModel> menu, int index);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetAccelerator(CefRefPtr<CefMenuModel> menu, int command_id, int key_code, BOOL shift_pressed, BOOL ctrl_pressed, BOOL alt_pressed);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetAcceleratorAt(CefRefPtr<CefMenuModel> menu, int index, int key_code, BOOL shift_pressed, BOOL ctrl_pressed, BOOL alt_pressed);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_RemoveAccelerator(CefRefPtr<CefMenuModel> menu, int command_id);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_RemoveAcceleratorAt(CefRefPtr<CefMenuModel> menu, int index);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_GetAccelerator(CefRefPtr<CefMenuModel> menu, int command_id, int& key_code, BOOL& shift_pressed, BOOL& ctrl_pressed, BOOL& alt_pressed);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_GetAcceleratorAt(CefRefPtr<CefMenuModel> menu, int index, int& key_code, BOOL& shift_pressed, BOOL& ctrl_pressed, BOOL& alt_pressed);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetColor(CefRefPtr<CefMenuModel> menu, int command_id, int color_type, int a, int r, int g, int b);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetColorAt(CefRefPtr<CefMenuModel> menu, int index, int color_type, int a, int r, int g, int b);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_GetColor(CefRefPtr<CefMenuModel> menu, int command_id, int color_type, int& a, int& r, int& g, int& b);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_GetColorAt(CefRefPtr<CefMenuModel> menu, int index, int color_type, int& a, int& r, int& g, int& b);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetFontList(CefRefPtr<CefMenuModel> menu, int command_id, const CefString& font_list);
DLLEXPORT BOOL TEXPORTS FBroHsMenuModel_SetFontListAt(CefRefPtr<CefMenuModel> menu, int index, const CefString& font_list);




DLLEXPORT int TEXPORTS FBroHsContextMenuParams_pGetXCoord(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT int TEXPORTS FBroHsContextMenuParams_pGetYCoord(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT int TEXPORTS FBroHsContextMenuParams_pGetTypeFlags(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsContextMenuParams_pGetLinkUrl(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsContextMenuParams_pGetUnfilteredLinkUrl(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsContextMenuParams_pGetSourceUrl(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsContextMenuParams_pGetPageUrl(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsContextMenuParams_pGetFrameCharset(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsContextMenuParams_pGetFrameUrl(CefRefPtr<CefContextMenuParams> params);

DLLEXPORT BOOL TEXPORTS FBroHsContextMenuParams_HasImageContents(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT int TEXPORTS FBroHsContextMenuParams_GetMediaType(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT int TEXPORTS FBroHsContextMenuParams_GetMediaStateFlags(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsContextMenuParams_GetSelectionText(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsContextMenuParams_GetMisspelledWord(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT CefRefPtr<FBroCefStringList> TEXPORTS FBroHsContextMenuParams_GetDictionarySuggestions(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT BOOL TEXPORTS FBroHsContextMenuParams_IsEditable(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT BOOL TEXPORTS FBroHsContextMenuParams_IsSpellCheckEnabled(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT int TEXPORTS FBroHsContextMenuParams_GetEditStateFlags(CefRefPtr<CefContextMenuParams> params);
DLLEXPORT BOOL TEXPORTS FBroHsContextMenuParams_IsCustomMenu(CefRefPtr<CefContextMenuParams> params);
//DLLEXPORT BOOL TEXPORTS FBroHsContextMenuParams_IsPepperMenu(CefRefPtr<CefContextMenuParams> params);

#endif // !_FBROELIB





///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#endif