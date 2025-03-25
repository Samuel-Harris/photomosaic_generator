from PhotomosaicGenerator import PhotomosaicGenerator


def main():
    target_path = "../christmas_party.jpeg"
    source_path = "../flamingos/"
    output_path = "../output.jpg"
    x_tiles = 60
    y_tiles = 100

    print("target: ", target_path)
    print("source: ", source_path)
    print("output: ", output_path)
    print("x-tiles: ", x_tiles)
    print("y-tiles: ", y_tiles)

    photomosaic_generator = PhotomosaicGenerator()
    photomosaic_generator.set_target_image(target_path)
    photomosaic_generator.set_input_directory_path(source_path)

    print("Pre-processing images...")
    photomosaic_generator.pre_process_images(x_tiles, y_tiles)

    print(f"{photomosaic_generator.get_num_images()} images pre-processed")

    print("generating photomosaic")
    photomosaic_generator.generate_photomosaic()

    photomosaic_generator.save_image(output_path)


if __name__ == "__main__":
    main()
