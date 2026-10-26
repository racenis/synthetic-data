#include <stdio.h>

#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_WRITE_IMPLEMENTATION

#include "stb_image.h"
#include "stb_image_write.h"

#include "../library/image.h"
#include "../library/quilt.h"

int main(int argc, const char** argv) {
	(void)argc;
	(void)argv;
	
	int width, height, channels;
	char* pixels = stbi_load("input.png", &width, &height, &channels, 3);

	if (pixels == NULL) {
		printf("Error: Could not load image.\n");
		return 1;
	}
	printf("Loaded: %dx%d, %d channels\n", width, height, channels);
	
	quilt_image_t input;
	quilt_image_t quilt;
	
	quilt_image_from_pixels(&input, pixels, width, height);
	
	//quilt_image_init(&quilt, width, height, 255, 255, 0);
	quilt_image_init(&quilt, width, height, 0, 0, 0);
	//quilt_image_copy(&input, &quilt);
	quilt_quilt(&input, &quilt);
	
	stbi_image_free(pixels);
	
	width = width + width;
	height = height + height;
	pixels = malloc(width * height * 3);
	quilt_image_to_pixels_border(&quilt, pixels);
	
	int success = stbi_write_png("output.png", width, height, 3, pixels, width * 3);

	if (!success) {
		printf("Error: Could not write image.\n");
	}
	
	return 0;
}