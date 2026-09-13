#pragma once
#ifndef FBROWSER_X509CERTIFICATE_H_
#define FBROWSER_X509CERTIFICATE_H_

class FBroBinaryValueList;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<CefX509CertPrincipal> TEXPORTS FBroHsX509Certificate_GetSubject(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT CefRefPtr<CefX509CertPrincipal> TEXPORTS FBroHsX509Certificate_GetIssuer(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsX509Certificate_GetSerialNumber(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsX509Certificate_GetDEREncoded(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsX509Certificate_GetPEMEncoded(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT time_t TEXPORTS FBroHsX509Certificate_GetValidStart(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT time_t TEXPORTS FBroHsX509Certificate_GetValidExpiry(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT size_t TEXPORTS FBroHsX509Certificate_GetIssuerChainSize(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT CefRefPtr<FBroBinaryValueList> TEXPORTS FBroHsX509Certificate_GetDEREncodedIssuerChain(CefRefPtr<CefX509Certificate> X509Certificate);
DLLEXPORT CefRefPtr<FBroBinaryValueList> TEXPORTS FBroHsX509Certificate_GetPEMEncodedIssuerChain(CefRefPtr<CefX509Certificate> X509Certificate);

#endif // !_FBROELIB




/// ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#endif // !FBROX509CERTIFICATE_H_