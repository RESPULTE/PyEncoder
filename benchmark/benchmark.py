def main():
    import os
    import time
    import difflib
    import tempfile

    from pyencoder.ArithmeticCoding import AdaptiveArithmeticCoding, StaticArithmeticCoding
    from pyencoder.HuffmanCoding import AdaptiveHuffmanCoding, StaticHuffmanCoding

    filename = "hamlet.txt"
    sigfig = 5

    dirname = os.path.dirname(__file__)
    filedir = os.path.join(dirname, filename)

    print(f"file selected: {filedir}")

    filesize = os.path.getsize(filedir)
    entropy_coding_algorithms = [
        StaticArithmeticCoding,
        AdaptiveArithmeticCoding,
        AdaptiveHuffmanCoding,
        StaticHuffmanCoding,
    ]

    for algo in entropy_coding_algorithms:
        print(f"[SELECTED]: '{algo.__name__.split('.')[-1]}")
        print("-------------------------------------------------")

        with open(filedir, "r") as file_to_encode, tempfile.NamedTemporaryFile(mode="wb+") as encoded_file:
            print(f"encoding ...")

            start_encode = time.perf_counter()

            algo.dump(file_to_encode, encoded_file)

            encoded_file.seek(0)
            file_to_encode.seek(0)

            end_encode = time.perf_counter()
            time_taken_encode = end_encode - start_encode
            print("[DONE]: time taken '{0:0.{1}f} sec'".format(time_taken_encode, sigfig))

            with tempfile.NamedTemporaryFile(mode="r+") as decoded_file:
                print(f"decoding ...")

                start_decode = time.perf_counter()

                algo.load(encoded_file, decoded_file)
                decoded_file.seek(0)

                end_decode = time.perf_counter()
                time_taken_decode = end_decode - start_decode
                print("[DONE]: time taken '{0:0.{1}f} sec'".format(time_taken_decode, sigfig))

                print("checking file integerity...")
                data_1, data_2 = decoded_file.read(), file_to_encode.read()
                if data_1 != data_2:
                    print("[FAILED]: decoded file does not match original file")
                    raise RuntimeError("you goofed up bro")

                print(
                    "[SUCCESS]:compression_ratio {0:0.{3}f} | encode_decode_ratio: {2:0.{3}f} | total_time: {1:0.{3}f} sec".format(
                        (filesize / os.path.getsize(encoded_file.name)),
                        end_decode - start_encode,
                        time_taken_encode / time_taken_decode,
                        sigfig,
                    )
                )
                print("-------------------------------------------------", "\n")


if __name__ == "__main__":
    main()
