#pragma once
#ifndef FBROWSER_SSLINFO_H_
#define FBROWSER_SSLINFO_H_

#ifndef _FBROELIB

DLLEXPORT int TEXPORTS FBroHsSSLInfo_GetCertStatus(CefRefPtr<CefSSLInfo> SSLInfo);
DLLEXPORT CefRefPtr<CefX509Certificate> TEXPORTS FBroHsSSLInfo_GetX509Certificate(CefRefPtr<CefSSLInfo> SSLInfo);

#endif // !_FBROELIB




#endif