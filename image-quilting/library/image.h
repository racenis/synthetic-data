#ifndef IMAGE_H
#define IMAGE_H

typedef struct {
	int width;
	int height;
	
	int* r;
	int* g;
	int* b;
} quilt_image_t;

void quilt_image_from_pixels(quilt_image_t* image, const char* pixels, int width, int height);
void quilt_image_copy(quilt_image_t* source, quilt_image_t* dest);
void quilt_image_init(quilt_image_t* image, int width, int height, int r, int g, int b);

void quilt_image_clear(quilt_image_t* image);

void quilt_image_to_pixels(quilt_image_t* image, const char* pixels);
void quilt_image_to_pixels_border(quilt_image_t* image, const char* pixels);

int quilt_image_sample_r(quilt_image_t* image, int x, int y);
int quilt_image_sample_g(quilt_image_t* image, int x, int y);
int quilt_image_sample_b(quilt_image_t* image, int x, int y);

int quilt_image_write_r(quilt_image_t* image, int x, int y, int value);
int quilt_image_write_g(quilt_image_t* image, int x, int y, int value);
int quilt_image_write_b(quilt_image_t* image, int x, int y, int value);

#endif // IMAGE_H