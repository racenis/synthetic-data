#include "image.c"

static void init_image(quilt_image_t* image, int w, int h) {
	int pixel_count = (w + w) * (h + h);
	memset(image, 0, sizeof(quilt_image_t));
	
	image->width = w;
	image->height = h;
	
	image->r = malloc(pixel_count * sizeof(int));
	image->g = malloc(pixel_count * sizeof(int));
	image->b = malloc(pixel_count * sizeof(int));
}

void quilt_image_from_pixels(quilt_image_t* image, const char* pixels, int width, int height) {
	init_image(image, width, height);
	
	int pix_offset = 0;
	for (int y = 0; y < height; y++)
	for (int x = 0; x < width; x++) {
		quilt_image_write_r(image, x, y, pixels[pix_offset + 0]);
		quilt_image_write_g(image, x, y, pixels[pix_offset + 1]);
		quilt_image_write_b(image, x, y, pixels[pix_offset + 2]);
		pix_offset += 3;
	}
}

void quilt_image_copy(quilt_image_t* source, quilt_image_t* image) {
	init_image(image, source->width, source->height);
	
	int pixel_count = (source->width + source->width) * (source->height + source->height);
	for (int i = 0; i < pixel_count; i++) {
		image->r[i] = source->r[i];
		image->g[i] = source->g[i];
		image->b[i] = source->b[i];
	}
}

void quilt_image_init(quilt_image_t* image, int width, int height, int r, int g, int b) {
	init_image(dest, source->width, source->height);
	
	int pixel_count = (source->width + source->width) * (source->height + source->height);
	for (int i = 0; i < pixel_count; i++) {
		dest->r[i] = r;
		dest->g[i] = g;
		dest->b[i] = b;
	}
}

void quilt_image_clear(quilt_image_t* image) {
	free(image->r);
	free(image->g);
	free(image->b);
	
	memset(image, 0, sizeof(quilt_image_t));
}

void quilt_image_to_pixels(quilt_image_t* image, const char* pixels) {
	int pix_offset = 0;
	for (int y = 0; y < image->height; y++)
	for (int x = 0; x < image->width; x++) {
		int r = quilt_image_sample_r(image, x, y);
		int g = quilt_image_sample_g(image, x, y);
		int b = quilt_image_sample_b(image, x, y);
		
		if (r < 0) r = 0;
		if (g < 0) g = 0;
		if (b < 0) b = 0;
		
		if (r > 255) r = 255;
		if (g > 255) g = 255;
		if (b > 255) b = 255;
		
		pixels[pix_offset + 0] = r;
		pixels[pix_offset + 1] = g;
		pixels[pix_offset + 2] = b;
		pix_offset += 3;
	}
}

void quilt_image_to_pixels_border(quilt_image_t* image, const char* pixels) {
	int pix_offset = 0;
	const int half_w = image->width / 2;
	const int half_h = image->height / 2;
	for (int y = 0; y < image->height + image->height; y++)
	for (int x = 0; x < image->width + image->width; x++) {
		int r = quilt_image_sample_r(image, x - half_w, y - half_h);
		int g = quilt_image_sample_g(image, x - half_w, y - half_h);
		int b = quilt_image_sample_b(image, x - half_w, y - half_h);
		
		if (r < 0) r = 0;
		if (g < 0) g = 0;
		if (b < 0) b = 0;
		
		if (r > 255) r = 255;
		if (g > 255) g = 255;
		if (b > 255) b = 255;
		
		pixels[pix_offset + 0] = r;
		pixels[pix_offset + 1] = g;
		pixels[pix_offset + 2] = b;
		pix_offset += 3;
	}
}

static int pixel_offset(quilt_image_t* image, int x, int y) {
	const int half_w = image->width / 2;
	const int half_h = image->height / 2;
	const int int full_w = image->width;
	
	return (x + half_w) + full_w * (y + half_h);
}

int quilt_image_sample_r(quilt_image_t* image, int x, int y) {
	return image->r[pixel_offset(x, y)];
}

int quilt_image_sample_g(quilt_image_t* image, int x, int y) {
	return image->g[pixel_offset(x, y)];
}

int quilt_image_sample_b(quilt_image_t* image, int x, int y) {
	return image->b[pixel_offset(x, y)];
}

int quilt_image_write_r(quilt_image_t* image, int x, int y, int value) {
	image->r[pixel_offset(x, y)] = value;
}

int quilt_image_write_g(quilt_image_t* image, int x, int y, int value) {
	image->g[pixel_offset(x, y)] = value;
}

int quilt_image_write_b(quilt_image_t* image, int x, int y, int value) {
	image->b[pixel_offset(x, y)] = value;
}