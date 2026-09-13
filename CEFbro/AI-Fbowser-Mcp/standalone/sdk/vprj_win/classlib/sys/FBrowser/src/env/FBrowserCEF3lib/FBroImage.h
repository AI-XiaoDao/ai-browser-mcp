#pragma once
#ifndef FBROWSER_IMAGE_H_
#define FBROWSER_IMAGE_H_

#ifndef _FBROELIB

DLLEXPORT BOOL TEXPORTS FBroHsImage_IsEmpty(CefRefPtr<CefImage> image);
DLLEXPORT int TEXPORTS FBroHsImage_GetWidth(CefRefPtr<CefImage> image);
DLLEXPORT int TEXPORTS FBroHsImage_GetHeight(CefRefPtr<CefImage> image);
DLLEXPORT BOOL TEXPORTS FBroHsImage_GetRepresentationInfo(CefRefPtr<CefImage> image, float scale_factor, float& actual_scale_factor, int& pixel_width, int& pixel_height);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsImage_GetAsBitmap(CefRefPtr<CefImage> image, float scale_factor, int colortype, int alphatype, int& pixel_width, int& pixel_height);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsImage_GetAsJPEG(CefRefPtr<CefImage> image, float scale_factor, int quality, int& pixel_width, int& pixel_height);
DLLEXPORT CefRefPtr<CefBinaryValue> TEXPORTS FBroHsImage_GetAsPNG(CefRefPtr<CefImage> image, float scale_factor, bool with_transparency, int& pixel_width, int& pixel_height);

#endif // !_FBROELIB





#endif


