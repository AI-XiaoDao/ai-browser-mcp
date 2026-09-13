#pragma once
#ifndef FBROWSER_SETCONTROL_H_
#define FBROWSER_SETCONTROL_H_

void WindowInfoSetControl(CefWindowInfo& info, PTELIB_WINDOWS_INFO windowsinfo);
void BrowserSettingsControl(CefBrowserSettings& browser_settings, FBroBrowserSetting* browserset);
void CefBrowserSetToEBrowserSet(CefBrowserSettings browser_settings, FBroBrowserSetting &browserset);


void EWindowInfoToCefWindowInfo(E_WINDOWS_INFO e_windowInfo, CefWindowInfo& windowInfo);
void CefWindowInfoToEWindowInfo(CefWindowInfo& windowInfo, E_WINDOWS_INFO &e_windowInfo);

void ReleaseEBrowserSet(FBroBrowserSetting* browserset);
void ReleaseEWindowInfo(PTELIB_WINDOWS_INFO e_windowInfo);


void SetClipChildStyle(HWND windowhwnd);

#endif