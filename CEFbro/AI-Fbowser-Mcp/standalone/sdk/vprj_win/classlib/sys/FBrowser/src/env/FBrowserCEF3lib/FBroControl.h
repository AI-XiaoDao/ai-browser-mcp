#pragma once
#ifndef FBROWSER_CONTROL_H_
#define FBROWSER_CONTROL_H_

class FBroString;
class FBroHsBroEvent;

extern HWND hide_window_;

#ifndef _FBROELIB
//创建浏览
DLLEXPORT BOOL TEXPORTS FBroHsCreate(const CefString& url, PTELIB_WINDOWS_INFO windowsinfo, FBroBrowserSetting* browsersetinfo,CefRefPtr<CefRequestContext> request, CefRefPtr<CefDictionaryValue> extrainfo, CefRefPtr<FBroHsBroEvent> hsbroevent, Event_Disable_Control* eventContrl, const CefString&);

//同步创建浏览
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsCreateSync(const CefString& url, PTELIB_WINDOWS_INFO windowsinfo, FBroBrowserSetting* browsersetinfo,CefRefPtr<CefRequestContext> request, CefRefPtr<CefDictionaryValue> extrainfo, CefRefPtr<FBroHsBroEvent> hsbroevent, Event_Disable_Control*, const CefString&);

//创建后台浏览
DLLEXPORT BOOL TEXPORTS FBroHsCreateBackground(const CefString& url, FBroBrowserSetting* browsersetinfo,CefRefPtr<CefRequestContext> request, CefRefPtr<CefDictionaryValue> extrainfo, CefRefPtr<FBroHsBroEvent> hsbroevent, Event_Disable_Control* eventContrl, const CefString&);

//同步创建后台浏览器
DLLEXPORT CefRefPtr<CefBrowser> TEXPORTS FBroHsCreateBackgroundSync(const CefString& url, FBroBrowserSetting* browsersetinfo,CefRefPtr<CefRequestContext> request, CefRefPtr<CefDictionaryValue> extrainfo, CefRefPtr<FBroHsBroEvent> hsbroevent, Event_Disable_Control* eventContrl, const CefString&);

DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBase64Encode(const CefString& data);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsBase64Decode(const CefString& data);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsGetDataURI(const CefString& mime_type, const CefString& data);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsURIEncode(const CefString& data, BOOL use_plus);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsURIDecode(const CefString& data, BOOL convert_to_utf8, int unescape_rule);
DLLEXPORT CefRefPtr<CefValue> TEXPORTS FBroHsParseJSON(const CefString& data, int options);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsWriteJSON(CefRefPtr<CefValue> node, int options);
DLLEXPORT CefRefPtr<CefValue> TEXPORTS FBroHsParseJSON_BinaryValue(CefRefPtr<CefBinaryValue> binaryvalue, int options);

#endif // !_FBROELIB



#endif




