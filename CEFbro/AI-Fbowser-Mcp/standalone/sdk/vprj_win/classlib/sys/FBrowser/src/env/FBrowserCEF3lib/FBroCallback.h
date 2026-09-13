#pragma once
#ifndef FBROWSER_CALLBACK_H_
#define FBROWSER_CALLBACK_H_

class FBroCefStringList;

#ifndef _FBROELIB
//DLLEXPORT void FBroRequestCallbackContinue_Continue(CefRefPtr<CefRequestCallback> callback, bool allow);新内核取消
DLLEXPORT void FBroSelectClientCertificateCallback_Select(CefRefPtr<CefSelectClientCertificateCallback> callback, CefRefPtr<CefX509Certificate> cert);
DLLEXPORT void FBroAuthCallback_Continue(CefRefPtr<CefAuthCallback> callback, const CefString& username, const CefString& password);
DLLEXPORT void FBroRunContextMenuCallback_Continue(CefRefPtr<CefRunContextMenuCallback> callback, int command_id, cef_event_flags_t event_flags);
DLLEXPORT void FBroRunContextMenuCallback_Cancel(CefRefPtr<CefRunContextMenuCallback> callback);
DLLEXPORT void FBroFileDialogCallback_Continue(CefRefPtr<CefFileDialogCallback> callback, /*int selected_accept_filter,新内核取消*/ CefRefPtr<FBroCefStringList> infilepaths);
DLLEXPORT void FBroFileDialogCallback_Cancel(CefRefPtr<CefFileDialogCallback> callback);
DLLEXPORT void FBroJSDialogCallback_Continue(CefRefPtr<CefJSDialogCallback> callback, BOOL success, const CefString& user_input);
DLLEXPORT void FBroJSFunctionCallback_Success(CefRefPtr<CefMessageRouterBrowserSide::Handler::Callback> callback, const CefString& response);
DLLEXPORT void FBroJSFunctionCallback_Failure(CefRefPtr<CefMessageRouterBrowserSide::Handler::Callback> callback, int error_code, const CefString& error_message);
DLLEXPORT void FBroCallback_Continue(CefRefPtr<CefCallback> callback);
DLLEXPORT void FBroCallback_Cancel(CefRefPtr<CefCallback> callback);
DLLEXPORT void FBroResourceSkipCallback_Continue(CefRefPtr<CefResourceSkipCallback> callback, int64_t bytes_skipped);
DLLEXPORT void FBroResourceReadCallback_Continue(CefRefPtr<CefResourceReadCallback> callback, int64_t bytes_read);
DLLEXPORT void FBroHsBeforeDownloadCallback_Continue(CefRefPtr<CefBeforeDownloadCallback> download, const CefString& lpBuffer, bool show_dialog);
DLLEXPORT void FBroHsBeforeDownloadCallback_Cancel(CefRefPtr<CefDownloadItemCallback> download);
DLLEXPORT void FBroHsBeforeDownloadCallback_Pause(CefRefPtr<CefDownloadItemCallback> download);
DLLEXPORT void FBroHsBeforeDownloadCallback_Resume(CefRefPtr<CefDownloadItemCallback> download);

DLLEXPORT void  FBroSchemeRegistrar_AddCustomScheme(CefRawPtr<CefSchemeRegistrar> registrar, const CefString& scheme_name, int options);

//DLLEXPORT void FBroGetExtensionResourceCallback_Continue(CefRawPtr<CefGetExtensionResourceCallback> callback, CefRefPtr<CefStreamReader> stream);
//DLLEXPORT void FBroGetExtensionResourceCallback_Cancel(CefRawPtr<CefGetExtensionResourceCallback> callback);

DLLEXPORT void FBroHsRunQuickMenuCallback_Continue(CefRefPtr<CefRunQuickMenuCallback> callback, int command_id, int event_flags);
DLLEXPORT void FBroHsRunQuickMenuCallback_Cancel(CefRefPtr<CefRunQuickMenuCallback> callback);

DLLEXPORT void FBroHsMediaAccessCallback_Continue(CefRefPtr<CefMediaAccessCallback> callback, int allowed_permissions);
DLLEXPORT void FBroHsMediaAccessCallback_Cancel(CefRefPtr<CefMediaAccessCallback> callback);

DLLEXPORT void FBroHsPermissionPromptCallback_Continue(CefRefPtr<CefPermissionPromptCallback> callback, int result);

#endif



#endif