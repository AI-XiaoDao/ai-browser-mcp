#pragma once
#ifndef FBROWSER_DRAGDATA_H_
#define FBROWSER_DRAGDATA_H_

class FBroString;

#ifndef _FBROELIB
DLLEXPORT CefRefPtr<CefDragData> TEXPORTS FBroHsDragData_Create();
DLLEXPORT CefRefPtr<CefDragData> TEXPORTS FBroHsDragData_Clone(CefRefPtr<CefDragData> DragData);
DLLEXPORT BOOL TEXPORTS FBroHsDragData_IsReadOnly(CefRefPtr<CefDragData> DragData);
DLLEXPORT BOOL TEXPORTS FBroHsDragData_IsLink(CefRefPtr<CefDragData> DragData);
DLLEXPORT BOOL TEXPORTS FBroHsDragData_IsFragment(CefRefPtr<CefDragData> DragData);
DLLEXPORT BOOL TEXPORTS FBroHsDragData_IsFile(CefRefPtr<CefDragData> DragData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDragData_GetLinkURL(CefRefPtr<CefDragData> DragData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDragData_GetLinkTitle(CefRefPtr<CefDragData> DragData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDragData_GetLinkMetadata(CefRefPtr<CefDragData> DragData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDragData_GetFragmentText(CefRefPtr<CefDragData> DragData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDragData_GetFragmentHtml(CefRefPtr<CefDragData> DragData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDragData_GetFragmentBaseURL(CefRefPtr<CefDragData> DragData);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDragData_GetFileName(CefRefPtr<CefDragData> DragData);
DLLEXPORT void TEXPORTS FBroHsDragData_SetLinkURL(CefRefPtr<CefDragData> DragData, const CefString& inData);
DLLEXPORT void TEXPORTS FBroHsDragData_SetLinkTitle(CefRefPtr<CefDragData> DragData, const CefString& inData);
DLLEXPORT void TEXPORTS FBroHsDragData_SetLinkMetadata(CefRefPtr<CefDragData> DragData, const CefString& inData);
DLLEXPORT void TEXPORTS FBroHsDragData_SetFragmentText(CefRefPtr<CefDragData> DragData, const CefString& inData);
DLLEXPORT void TEXPORTS FBroHsDragData_SetFragmentHtml(CefRefPtr<CefDragData> DragData, const CefString& inData);
DLLEXPORT void TEXPORTS FBroHsDragData_SetFragmentBaseURL(CefRefPtr<CefDragData> DragData, const CefString& inData);
DLLEXPORT void TEXPORTS FBroHsDragData_AddFile(CefRefPtr<CefDragData> DragData, const CefString& path, const CefString& display_name);
DLLEXPORT CefRefPtr<CefImage> TEXPORTS FBroHsDragData_GetImage(CefRefPtr<CefDragData> DragData);
DLLEXPORT void TEXPORTS FBroHsDragData_GetImageHotspot(CefRefPtr<CefDragData> DragData, PTELIB_ELEMENT_AT retpoint);
DLLEXPORT BOOL TEXPORTS FBroHsDragData_HasImage(CefRefPtr<CefDragData> DragData);
#endif // !_FBROELIB



#endif
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
