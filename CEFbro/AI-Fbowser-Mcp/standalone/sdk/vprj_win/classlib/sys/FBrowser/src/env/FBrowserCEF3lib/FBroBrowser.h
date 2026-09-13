#ifndef FBROWSER_BROWSER_H_
#define FBROWSER_BROWSER_H_

class FBroCefStringList;
class FBroHsClearCacheCallback;
class FBroString;

#ifndef _FBROELIB

DLLEXPORT BOOL TEXPORTS FBroHsBrowser_CanGoBack(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowser_GoBack(CefRefPtr<CefBrowser> browser);
DLLEXPORT BOOL TEXPORTS FBroHsBrowser_CanGoForward(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowser_GoForward(CefRefPtr<CefBrowser> browser);
DLLEXPORT BOOL TEXPORTS FBroHsBrowser_IsLoading(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowser_Reload(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowser_ReloadIgnoreCache(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowser_StopLoad(CefRefPtr<CefBrowser> browser);
DLLEXPORT int TEXPORTS FBroHsBrowser_GetIdentifier(CefRefPtr<CefBrowser> browser);
DLLEXPORT BOOL TEXPORTS FBroHsBrowser_IsSame(CefRefPtr<CefBrowser> browser, CefRefPtr<CefBrowser> that);
DLLEXPORT BOOL TEXPORTS FBroHsBrowser_IsPopup(CefRefPtr<CefBrowser> browser);
DLLEXPORT BOOL TEXPORTS FBroHsBrowser_HasDocument(CefRefPtr<CefBrowser> browser);
DLLEXPORT CefRefPtr<CefFrame> TEXPORTS FBroHsBrowser_GetMainFrame(CefRefPtr<CefBrowser> browser);
DLLEXPORT CefRefPtr<CefFrame> TEXPORTS FBroHsBrowser_GetFocusedFrame(CefRefPtr<CefBrowser> browser);
DLLEXPORT CefRefPtr<CefFrame> TEXPORTS FBroHsBrowser_GetFrameById(CefRefPtr<CefBrowser> browser, const CefString& identifier);
DLLEXPORT CefRefPtr<CefFrame> TEXPORTS FBroHsBrowser_GetFrameByName(CefRefPtr<CefBrowser> browser, const CefString& name);
DLLEXPORT CefRefPtr<FBroCefStringList> TEXPORTS FBroHsBrowser_GetFrameIdentifiers(CefRefPtr<CefBrowser> browser);
DLLEXPORT CefRefPtr<FBroCefStringList> TEXPORTS FBroHsBrowser_GetFrameNames(CefRefPtr<CefBrowser> browser);


//额外功能
//清理缓存
DLLEXPORT void TEXPORTS FBroHsBrowser_ClearCacheData(CefRefPtr<CefBrowser> browser, const CefString& origin, unsigned long removeflag, unsigned long quotaflag, CefRefPtr<FBroHsClearCacheCallback> callback);
//清理全局缓存
DLLEXPORT void TEXPORTS FBroHsBrowser_ClearGlobalCacheData(const CefString& origin, unsigned long removeflag, unsigned long quotaflag, CefRefPtr<FBroHsClearCacheCallback> callback);

#endif // !_FBROELIB


//设置代理
DLLEXPORT void TEXPORTS FBroHsBrowser_SetProxy(CefRefPtr<CefBrowser> browser, const CefString& url, const CefString& user, const CefString& password);
DLLEXPORT void TEXPORTS FBroHsBrowser_SetProxy(CefRefPtr<CefBrowser> browser, const CefString& url, const CefString& user, const CefString& password);

//清理代理
DLLEXPORT void TEXPORTS FBroHsBrowser_ClearProxy(CefRefPtr<CefBrowser> browser);
DLLEXPORT void TEXPORTS FBroHsBrowser_ClearProxy(CefRefPtr<CefBrowser> browser);


DLLEXPORT CefRefPtr<CefDictionaryValue> TEXPORTS FBroHsBrowser_GetExtrainfo(CefRefPtr<CefBrowser> browser);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsBrowser_GetFlag(CefRefPtr<CefBrowser> browser);

#endif