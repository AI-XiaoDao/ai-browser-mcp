#pragma once
#ifndef FBROWSER_RESPONSE_H_
#define FBROWSER_RESPONSE_H_

class FBroString;
class FBroDoubleString;
#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefResponse> TEXPORTS FBroHsResponse_Create();
DLLEXPORT BOOL TEXPORTS FBroHsResponse_IsReadOnly(CefRefPtr<CefResponse> response);
DLLEXPORT int TEXPORTS FBroHsResponse_GetError(CefRefPtr<CefResponse> response);
DLLEXPORT void TEXPORTS FBroHsResponse_SetError(CefRefPtr<CefResponse> response, int error);
DLLEXPORT int TEXPORTS FBroHsResponse_GetStatus(CefRefPtr<CefResponse> response);
DLLEXPORT void TEXPORTS FBroHsResponse_SetStatus(CefRefPtr<CefResponse> response, int status);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsResponse_GetStatusText(CefRefPtr<CefResponse> response);
DLLEXPORT void TEXPORTS FBroHsResponse_SetStatusText(CefRefPtr<CefResponse> response, const CefString& statusText);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsResponse_GetMimeType(CefRefPtr<CefResponse> response);
DLLEXPORT void TEXPORTS FBroHsResponse_SetMimeType(CefRefPtr<CefResponse> response, const CefString& mimeType);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsResponse_GetCharset(CefRefPtr<CefResponse> response);
DLLEXPORT void TEXPORTS FBroHsResponse_SetCharset(CefRefPtr<CefResponse> response, const CefString& charset);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsResponse_GetHeaderByName(CefRefPtr<CefResponse> response, const CefString& name);
DLLEXPORT void TEXPORTS FBroHsResponse_SetHeaderByName(CefRefPtr<CefResponse> response, const CefString& name, const CefString& value, BOOL overwrite);
DLLEXPORT CefRefPtr<FBroDoubleString>  TEXPORTS FBroHsResponse_GetHeaderMap(CefRefPtr<CefResponse> response);

DLLEXPORT void TEXPORTS FBroHsResponse_DeleteHeaderMap(CefRefPtr<CefResponse> response, const CefString& key);
DLLEXPORT void TEXPORTS FBroHsResponse_SetHeaderMap(CefRefPtr<CefResponse> response, PTELIB_STRING_STRING inbuf);
DLLEXPORT void TEXPORTS FBroHsResponse_SetHeaderMap_Array(CefRefPtr<CefResponse> response, CefRefPtr<FBroDoubleString> indata, bool deleteother);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsResponse_GetURL(CefRefPtr<CefResponse> response);
DLLEXPORT void TEXPORTS FBroHsResponse_SetURL(CefRefPtr<CefResponse> response, const CefString& url);
#endif

///////////////////////////////////////////////////////////////////////////////////////////////////////

#endif

