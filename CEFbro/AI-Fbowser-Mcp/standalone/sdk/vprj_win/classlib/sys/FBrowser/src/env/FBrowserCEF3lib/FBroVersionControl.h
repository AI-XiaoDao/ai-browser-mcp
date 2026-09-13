#pragma once
#ifndef FBRO_VERSION_CONTROL_H
#define FBRO_VERSION_CONTROL_H

enum VersionType;

void FBroSetVersionShareMem(VersionType type);
VersionType FBroGetVersionShareMem();


#endif