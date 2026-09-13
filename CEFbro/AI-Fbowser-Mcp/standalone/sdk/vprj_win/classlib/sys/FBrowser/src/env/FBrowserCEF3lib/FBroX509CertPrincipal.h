#pragma once
#ifndef FBROWSER_X509CERTPRINCIPAL_H_
#define FBROWSER_X509CERTPRINCIPAL_H_

class FBroString;
class FBroCefStringList;

#ifndef _FBROELIB

DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsX509CertPrincipal_GetDisplayName(CefRefPtr<CefX509CertPrincipal> X509CertPrincipal);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsX509CertPrincipal_GetCommonName(CefRefPtr<CefX509CertPrincipal> X509CertPrincipal);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsX509CertPrincipal_GetLocalityName(CefRefPtr<CefX509CertPrincipal> X509CertPrincipal);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsX509CertPrincipal_GetStateOrProvinceName(CefRefPtr<CefX509CertPrincipal> X509CertPrincipal);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsX509CertPrincipal_GetCountryName(CefRefPtr<CefX509CertPrincipal> X509CertPrincipal);
DLLEXPORT CefRefPtr<FBroCefStringList> TEXPORTS FBroHsX509CertPrincipal_GetOrganizationNames(CefRefPtr<CefX509CertPrincipal> X509CertPrincipal);
DLLEXPORT CefRefPtr<FBroCefStringList> TEXPORTS FBroHsX509CertPrincipal_GetOrganizationUnitNames(CefRefPtr<CefX509CertPrincipal> X509CertPrincipal);


#endif // !_FBROELIB


#endif
/// ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
