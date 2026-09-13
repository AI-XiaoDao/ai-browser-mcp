#pragma once
#ifndef FBROWSER_DOM_H_
#define FBROWSER_DOM_H_

class FBroString;
class FBroDoubleString;

#ifndef _FBROELIB
DLLEXPORT int TEXPORTS FBroHsDOMNode_GetType(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_IsText(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_IsElement(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_IsEditable(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_IsFormControlElement(CefRefPtr<CefDOMNode> object);
DLLEXPORT int TEXPORTS FBroHsDOMNode_GetFormControlElementType(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_IsSame(CefRefPtr<CefDOMNode> object, CefRefPtr<CefDOMNode> that);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMNode_GetName(CefRefPtr<CefDOMNode> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMNode_GetValue(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_SetValue(CefRefPtr<CefDOMNode> object, const CefString& indata);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMNode_GetAsMarkup(CefRefPtr<CefDOMNode> object);
DLLEXPORT CefRefPtr<CefDOMDocument> TEXPORTS FBroHsDOMNode_GetDocument(CefRefPtr<CefDOMNode> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMNode_GetParent(CefRefPtr<CefDOMNode> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMNode_GetPreviousSibling(CefRefPtr<CefDOMNode> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMNode_GetNextSibling(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_HasChildren(CefRefPtr<CefDOMNode> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMNode_GetFirstChild(CefRefPtr<CefDOMNode> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMNode_GetLastChild(CefRefPtr<CefDOMNode> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMNode_GetElementTagName(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_HasElementAttributes(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_HasElementAttributes_Name(CefRefPtr<CefDOMNode> object, const CefString& name);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMNode_GetElementAttribute(CefRefPtr<CefDOMNode> object, const CefString& attrName);
DLLEXPORT CefRefPtr<FBroDoubleString> TEXPORTS FBroHsDOMNode_GetElementAttributes(CefRefPtr<CefDOMNode> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMNode_SetElementAttribute(CefRefPtr<CefDOMNode> object, const CefString& attrName, const CefString& value);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMNode_GetElementInnerText(CefRefPtr<CefDOMNode> object);
DLLEXPORT void TEXPORTS FBroHsDOMNode_GetElementBounds(CefRefPtr<CefDOMNode> object, POINT_RECT retdata);

DLLEXPORT int TEXPORTS FBroHsDOMDocument_GetType(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMDocument_GetDocument(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMDocument_GetBody(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMDocument_GetHead(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMDocument_GetTitle(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMDocument_GetElementById(CefRefPtr<CefDOMDocument> object, const CefString& id);
DLLEXPORT CefRefPtr<CefDOMNode> TEXPORTS FBroHsDOMDocument_GetFocusedNode(CefRefPtr<CefDOMDocument> object);
DLLEXPORT BOOL TEXPORTS FBroHsDOMDocument_HasSelection(CefRefPtr<CefDOMDocument> object);
DLLEXPORT int TEXPORTS FBroHsDOMDocument_GetSelectionStartOffset(CefRefPtr<CefDOMDocument> object);
DLLEXPORT int TEXPORTS FBroHsDOMDocument_GetSelectionEndOffset(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMDocument_GetSelectionAsMarkup(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMDocument_GetSelectionAsText(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMDocument_GetBaseURL(CefRefPtr<CefDOMDocument> object);
DLLEXPORT CefRefPtr<FBroString> TEXPORTS FBroHsDOMDocument_GetCompleteURL(CefRefPtr<CefDOMDocument> object, const CefString& partialURL);

#endif // !_FBROELIB


#endif
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
