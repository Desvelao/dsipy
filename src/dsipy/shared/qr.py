import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_qr(
    image: str = "",
    output: str = "",
    data: str = "",
    caption_top: str = "",
    caption_bottom: str = "",
    font: str = "",
):
    """
    Generate a QR code
    """

    if not output:
        raise ValueError("Output file path is required")

    if not data:
        raise ValueError("Data for QR code is required")
    # import modules

    QRcode = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)

    # adding URL or text to QRcode
    QRcode.add_data(data)

    # generating QR code
    QRcode.make()

    # taking color name from user
    QRcolor = "Green"
    # adding color to QR code
    # QRimg = QRcode.make_image(
    #     fill_color=QRcolor, back_color="white").convert('RGB')

    QRimg = QRcode.make_image(fill_color="Black", back_color="white").convert("RGB")

    # taking image which user wants
    # in the QR code center

    if image:
        logo_img = Image.open(image)

        # taking base width
        basewidth = 100

        # adjust image size
        wpercent = basewidth / float(logo_img.size[0])
        hsize = int((float(logo_img.size[1]) * float(wpercent)))
        logo_img = logo_img.resize((basewidth, hsize), Image.LANCZOS)

        # set size of QR code
        pos = (
            (QRimg.size[0] - logo_img.size[0]) // 2,
            (QRimg.size[1] - logo_img.size[1]) // 2,
        )
        QRimg.paste(logo_img, pos)

    if caption_top:
        # font = "NotoSans-Black.ttf"
        if not font:
            raise ValueError("Font file is required for caption")
        draw = ImageDraw.Draw(QRimg)
        qr_width, qr_height = QRimg.size
        font_size = 1  # starting font size
        img_fraction = 0.90  # portion of image width you want text width to be, I've had good luck with .90
        # TODO: fix offset
        font_height_max = QRcode.border * QRcode.box_size - 18
        caption_x = 0
        caption_y = 0
        font = ImageFont.truetype(font, font_size)
        while (
            font.getbbox(caption_top)[2] - font.getbbox(caption_top)[0]
            < img_fraction * qr_width
            and font.getbbox(caption_top)[3] - font.getbbox(caption_top)[1]
            < font_height_max
        ):
            font_size += 1
            font = ImageFont.truetype(font, font_size)
        caption_x = (
            int(qr_width - font.getbbox(caption_top)[2] - font.getbbox(caption_top)[0])
            / 2
        )  # Center the label
        draw.text((caption_x, caption_y), caption_top, font=font, fill=(0, 0, 0, 255))

    if caption_bottom:
        # font = "NotoSans-Black.ttf"
        if not font:
            raise ValueError("Font file is required for caption")
        draw = ImageDraw.Draw(QRimg)
        qr_width, qr_height = QRimg.size
        font_size = 1  # starting font size
        img_fraction = 0.90  # portion of image width you want text width to be, I've had good luck with .90
        # TODO: fix offset
        font_height_max = QRcode.border * QRcode.box_size - 10
        caption_x = 0
        caption_y = 0
        font = ImageFont.truetype(font, font_size)
        while (
            font.getbbox(caption_bottom)[2] - font.getbbox(caption_bottom)[0]
            < img_fraction * qr_width
            and font.getbbox(caption_bottom)[3] - font.getbbox(caption_bottom)[1]
            < font_height_max
        ):
            font_size += 1
            font = ImageFont.truetype(font, font_size)
        caption_x = (
            int(
                qr_width
                - font.getbbox(caption_bottom)[2]
                - font.getbbox(caption_bottom)[0]
            )
            / 2
        )  # Center the label
        # TODO: fix offset
        caption_y = qr_height - font.size - 8
        draw.text(
            (caption_x, caption_y), caption_bottom, font=font, fill=(0, 0, 0, 255)
        )

    # save the QR code generated
    if output:
        QRimg.save(output)
    else:
        QRimg.show()

    print("QR code generated!")
