#pragma once
#ifndef FBROWSER_DOWNLOADITEM_H_
#define FBROWSER_DOWNLOADITEM_H_

class FBroString;

#ifndef _FBROELIB
DLLEXPORT BOOL TEXPORTS FBroHsDownloadItem_IsInProgress(CefRefPtr<CefDownloadItem> download);
DLLEXPORT BOOL TEXPORTS FBroHsDownloadItem_IsComplete(CefRefPtr<CefDownloadItem> download);
DLLEXPORT BOOL TEXPORTS FBroHsDownloadItem_IsCanceled(CefRefPtr<CefDownloadItem> download);
DLLEXPORT int64_t TEXPORTS FBroHsDownloadItem_GetCurrentSpeed(CefRefPtr<CefDownloadItem> download);
DLLEXPORT time_t TEXPORTS FBroHsDownloadItem_GetStartTime(CefRefPtr<CefDownloadItem> download);
DLLEXPORT time_t TEXPORTS FBroHsDownloadItem_GetEndTime(CefRefPtr<CefDownloadItem> download);
DLLEXPORT int TEXPORTS FBroHsDownloadItem_GetPercentComplete(CefRefPtr<CefDownloadItem> download);
DLLEXPORT int64_t TEXPORTS FBroHsDownloadItem_GetTotalBytes(CefRefPtr<CefDownloadItem> download);
DLLEXPORT int64_t TEXPORTS FBroHsDownloadItem_GetReceivedBytes(CefRefPtr<CefDownloadItem> download);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDownloadItem_GetFullPath(CefRefPtr<CefDownloadItem> download);
DLLEXPORT uint32_t TEXPORTS FBroHsDownloadItem_GetDownloadId(CefRefPtr<CefDownloadItem> download);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDownloadItem_GetDownloadURL(CefRefPtr<CefDownloadItem> download);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDownloadItem_GetDownloadOriginalUrl(CefRefPtr<CefDownloadItem> download);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDownloadItem_GetSuggestedFileName(CefRefPtr<CefDownloadItem> download);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDownloadItem_GetDownloadMimeType(CefRefPtr<CefDownloadItem> download);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDownloadItem_GetContentDisposition(CefRefPtr<CefDownloadItem> download);

#endif // !_FBROELIB



#endif