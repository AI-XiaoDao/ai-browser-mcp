#pragma once
#ifndef FBROWSER_REQUESTCONTEXT_H_
#define FBROWSER_REQUESTCONTEXT_H_

class FBroString;
class FBroHsExtensionHandler;
class FBroCefStringList;
class FBroHsResourceHandler;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefRequestContext> TEXPORTS FBroHsRequestContext_GetGlobalContext();
DLLEXPORT CefRefPtr<CefRequestContext> TEXPORTS FBroHsRequestContext_CreateContext(POINT_REQUSETCONTEXT_SET set);
DLLEXPORT CefRefPtr<CefRequestContext> TEXPORTS FBroHsRequestContext_CreateContextFromOther(CefRefPtr<CefRequestContext> otherRequestContext);
DLLEXPORT BOOL TEXPORTS FBroHsRequestContext_IsSame(CefRefPtr<CefRequestContext> RequestContext, CefRefPtr<CefRequestContext> otherRequestContext);
DLLEXPORT BOOL TEXPORTS FBroHsRequestContext_IsSharingWith(CefRefPtr<CefRequestContext> RequestContext, CefRefPtr<CefRequestContext> otherRequestContext);
DLLEXPORT BOOL TEXPORTS FBroHsRequestContext_IsGlobal(CefRefPtr<CefRequestContext> RequestContext);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsRequestContext_GetCachePath(CefRefPtr<CefRequestContext> RequestContext);
DLLEXPORT CefRefPtr<CefCookieManager> TEXPORTS FBroHsRequestContext_GetCookieManager(CefRefPtr<CefRequestContext> RequestContext);
DLLEXPORT BOOL TEXPORTS FBroHsRequestContext_HasPreference(CefRefPtr<CefRequestContext> RequestContext, const CefString& name);
DLLEXPORT CefRefPtr<CefValue> TEXPORTS FBroHsRequestContext_GetPreference(CefRefPtr<CefRequestContext> RequestContext, const CefString& name);
DLLEXPORT CefRefPtr<CefDictionaryValue> TEXPORTS FBroHsRequestContext_GetAllPreferences(CefRefPtr<CefRequestContext> RequestContext, BOOL include_defaults);
DLLEXPORT BOOL TEXPORTS FBroHsRequestContext_CanSetPreference(CefRefPtr<CefRequestContext> RequestContext, const CefString& name);
DLLEXPORT BOOL TEXPORTS FBroHsRequestContext_SetPreference(CefRefPtr<CefRequestContext> RequestContext, const CefString& name, CefRefPtr<CefValue> value, CefRefPtr<FBroString> fbroerror);

DLLEXPORT BOOL FBroHsRequestContext_RegisterSchemeHandlerFactory(CefRefPtr<CefRequestContext> RequestContext, const CefString& scheme_name, const CefString& domain_name, CefRefPtr<FBroHsResourceHandler> callback);
DLLEXPORT BOOL FBroHsRequestContext_ClearSchemeHandlerFactories(CefRefPtr<CefRequestContext> RequestContex);

#endif // !_FBROELIB




//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#endif