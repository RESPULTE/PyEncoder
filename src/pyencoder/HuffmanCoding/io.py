# def dump(
#     dataset: ValidDataset,
#     dtype: SupportedDataType,
#     file: BinaryIO,
#     *,
#     length_encoding: bool = False,
#     sof_marker: Optional[ValidData] = None,
#     eof_marker: Optional[ValidData] = None,
# ) -> None:
#     codebook, encoded_data = encode(dataset, dtype=dtype, length_encoding=length_encoding)

#     codelengths, symbols = generate_header_from_codebook(
#         codebook, dtype if not length_encoding else config.LENGTH_ENCODING_DATA_DTYPE
#     )

#     header_size = tobin(len(codelengths + symbols), config.HEADER_MARKER_DTYPE, bitlength=config.HEADER_MARKER_BITSIZE)

#     sof_marker = tobin(sof_marker or config.SOF_MARKER, config.MARKER_DTYPE, bitlength=config.MARKER_BITSIZE)
#     eof_marker = tobin(eof_marker or config.EOF_MARKER, config.MARKER_DTYPE, bitlength=config.MARKER_BITSIZE)

#     bin_data = tobytes(sof_marker + header_size + codelengths + symbols + encoded_data + eof_marker, "bin")
#     file.write(bin_data)

#     return bin_data


# def load(
#     file: BinaryIO,
#     dtype: SupportedDataType,
#     *,
#     length_encoding: bool = False,
#     sof_marker: Optional[ValidData] = None,
#     eof_marker: Optional[ValidData] = None,
# ) -> ValidDataset:
#     raw_bindata = frombytes(file.read(), "bin")

#     sof_marker = tobin(sof_marker or config.SOF_MARKER, config.MARKER_DTYPE, bitlength=config.MARKER_BITSIZE)
#     eof_marker = tobin(eof_marker or config.EOF_MARKER, config.MARKER_DTYPE, bitlength=config.MARKER_BITSIZE)

#     try:
#         raw_encoded_data = raw_bindata.split(sof_marker, maxsplit=1)[1].rsplit(eof_marker, maxsplit=1)[0]
#         if raw_encoded_data == "":
#             raise CorruptedEncodingError("faulty EOF or SOF marker")

#         header_size, huffman_data = (
#             frombin(raw_encoded_data[: config.HEADER_MARKER_BITSIZE], config.HEADER_MARKER_DTYPE),
#             raw_encoded_data[config.HEADER_MARKER_BITSIZE :],
#         )

#         header, encoded_data = huffman_data[:header_size], huffman_data[header_size:]

#         codebook = generate_codebook_from_header(
#             header, dtype if not length_encoding else config.LENGTH_ENCODING_DATA_DTYPE
#         )
#         return decode(codebook, encoded_data, dtype, length_encoding)

#     except Exception as err:
#         raise CorruptedEncodingError("encoding cannot be decoded") from err
