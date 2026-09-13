#pragma once
#ifndef FBROWSER_SHAREMEMORYREGION_H_
#define FBROWSER_SHAREMEMORYREGION_H_

class CefSharedMemoryRegion;

#ifndef _FBROELIB

DLLEXPORT BOOL TEXPORTS FBroHsSharedMemoryRegion_IsValid(CefRefPtr<CefSharedMemoryRegion> shareMemoryRegion);
DLLEXPORT int TEXPORTS FBroHsSharedMemoryRegion_Size(CefRefPtr<CefSharedMemoryRegion> shareMemoryRegion);
DLLEXPORT void TEXPORTS FBroHsSharedMemoryRegion_Memory(CefRefPtr<CefSharedMemoryRegion> shareMemoryRegion, void* retdata, int insize);

#endif !_FBROELIB

#endif