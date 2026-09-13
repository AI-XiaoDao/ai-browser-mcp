#pragma once
#include "FBroHsBaseEvent.h"

#ifndef _FBROELIB
DLLEXPORT void TEXPORTS FBroHsURLRequest_Create(CefRefPtr<CefRequest> request, CefRefPtr<CefRequestContext> request_context, CefRefPtr<FBroHsURLRequestClient> hsevent, int64_t flag);

DLLEXPORT CefRefPtr<CefRequest> TEXPORTS FBroHsURLRequest_GetRequest(CefRefPtr<CefURLRequest> urlrequest);
DLLEXPORT CefRefPtr<CefURLRequestClient> TEXPORTS FBroHsURLRequest_GetClient(CefRefPtr<CefURLRequest> urlrequest);
DLLEXPORT int TEXPORTS FBroHsURLRequest_GetRequestStatus(CefRefPtr<CefURLRequest> urlrequest);
DLLEXPORT int TEXPORTS FBroHsURLRequest_GetRequestError(CefRefPtr<CefURLRequest> urlrequest);
DLLEXPORT CefRefPtr<CefResponse> TEXPORTS FBroHsURLRequest_GetResponse(CefRefPtr<CefURLRequest> urlrequest);
DLLEXPORT BOOL TEXPORTS FBroHsURLRequest_ResponseWasCached(CefRefPtr<CefURLRequest> urlrequest);
DLLEXPORT void TEXPORTS FBroHsURLRequest_Cancel(CefRefPtr<CefURLRequest> urlrequest);
#endif