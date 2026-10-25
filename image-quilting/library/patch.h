#ifndef PATCH_H
#define PATCH_H

#include "image.h"

typedef struct {
	int width;
	int height;
	
	int x;
	int y;
	
	quilt_image_t* source;
} quilt_patch_t;

void quilt_patch_from_coords(quilt_image_t* source, int w, int h, int x, int y);
void quilt_patch_pick(quilt_image_t* source, quilt_image_t* dest, int w, int h, int x, int y);



#endif // PATCH_H