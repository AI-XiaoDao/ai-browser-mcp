#pragma once
#ifndef FBROWSER_REQUEST_H_
#define FBROWSER_REQUEST_H_

class FBroString;
class FBroDoubleString;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefRequest> TEXPORTS FBroHsRequest_Create();
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsRequest_GetURL(CefRefPtr<CefRequest> Request);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsRequest_GetMethod(CefRefPtr<CefRequest> Request);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsRequest_GetReferrerURL(CefRefPtr<CefRequest> Request);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsRequest_GetFirstPartyForCookies(CefRefPtr<CefRequest> Request);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsRequest_GetHeaderByName(CefRefPtr<CefRequest> Request, const CefString& name);
DLLEXPORT CefRefPtr<FBroDoubleString>  TEXPORTS FBroHsRequest_GetHeaderMap(CefRefPtr<CefRequest> Request);
DLLEXPORT void TEXPORTS FBroHsRequest_SetHeaderMap_Array(CefRefPtr<CefRequest> Request, CefRefPtr<FBroDoubleString> indata, bool deleteother);
DLLEXPORT uint64_t TEXPORTS FBroHsRequest_GetIdentifier(CefRefPtr<CefRequest> Request);

DLLEXPORT BOOL TEXPORTS FBroHsRequest_IsReadOnly(CefRefPtr<CefRequest> Request);
DLLEXPORT void TEXPORTS FBroHsRequest_SetURL(CefRefPtr<CefRequest> Request, const CefString& url);
DLLEXPORT void TEXPORTS FBroHsRequest_SetMethod(CefRefPtr<CefRequest> Request, const CefString& method);
DLLEXPORT void TEXPORTS FBroHsRequest_SetReferrer(CefRefPtr<CefRequest> Request, const CefString& referrer_url, int policy);
DLLEXPORT int TEXPORTS FBroHsRequest_GetReferrerPolicy(CefRefPtr<CefRequest> Request);
DLLEXPORT CefRefPtr<CefPostData> TEXPORTS FBroHsRequest_GetPostData(CefRefPtr<CefRequest> Request);
DLLEXPORT void TEXPORTS FBroHsRequest_SetPostData(CefRefPtr<CefRequest> Request, CefRefPtr<CefPostData> postData);
DLLEXPORT void TEXPORTS FBroHsRequest_DeleteHeaderMap(CefRefPtr<CefRequest> Request, const CefString& key);
DLLEXPORT void TEXPORTS FBroHsRequest_SetHeaderMap(CefRefPtr<CefRequest> Request, PTELIB_STRING_STRING indata);
DLLEXPORT void TEXPORTS FBroHsRequest_SetHeaderByName(CefRefPtr<CefRequest> Request, const CefString& name, const CefString& value, bool overwrite);
DLLEXPORT void TEXPORTS FBroHsRequest_Set(CefRefPtr<CefRequest> Request, const CefString& url, const CefString& method, CefRefPtr<CefPostData> postData, PTELIB_STRING_STRING inheaderMap);
DLLEXPORT int TEXPORTS FBroHsRequest_GetFlags(CefRefPtr<CefRequest> Request);
DLLEXPORT void TEXPORTS FBroHsRequest_SetFlags(CefRefPtr<CefRequest> Request, int flags);
DLLEXPORT void TEXPORTS FBroHsRequest_SetFirstPartyForCookies(CefRefPtr<CefRequest> Request, const CefString& url);
DLLEXPORT CefRequest::ResourceType TEXPORTS FBroHsRequest_GetResourceType(CefRefPtr<CefRequest> Request);
DLLEXPORT int64_t TEXPORTS FBroHsRequest_GetTransitionType(CefRefPtr<CefRequest> Request);

#endif // !_FBROELIB




#endif



