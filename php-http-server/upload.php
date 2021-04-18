<?php
/*
 * upload.php: Original work Copyright (C) 2021 by Blewett

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

 */
{
    // camera
    $camera = $_POST["camera"];
    if($camera == "")
    {
        print("Sorry, no camera was specified.\n");
        exit(0);
    }
    $directory = strtolower("archive/$camera");

    if (!is_dir("archive"))
        mkdir("archive", 0755);

    if (file_exists($directory) && !is_dir($directory))
	unlink($directory);

    $directory = $directory . "/";

    if (!is_dir($directory))
        mkdir($directory, 0755);

    $target_file = $directory . basename($_FILES["monitorFile"]["name"]);
    $imageFileType = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));
    // print($target_file . "  image type : " . $imageFileType . "\n");

    // check if file already exists
    if (file_exists($target_file))
    {
        print("Sorry, there is a file named \"" .
              $_FILES["monitorFile"]["name"] . 
              "\" already in the archive.\n");
        exit(0);
    }

    // limit the file size
    if ($_FILES["monitorFile"]["size"] > 20000000)
    {
        print("Sorry, your file is too large.\n");
        exit(0);
    }

    // limit the file formats
    if($imageFileType != "jpg" && $imageFileType != "png" &&
       $imageFileType != "jpeg" &&
       $imageFileType != "mp4" && $imageFileType != "webm")
    {
        print("Sorry, only mp4, webm, jpg, and jpeg files are allowed.\n");
        exit(0);
    }

    // upload and store the file
    if (move_uploaded_file($_FILES["monitorFile"]["tmp_name"], $target_file))
    {
        print("uploaded ($camera) " . basename($_FILES["monitorFile"]["name"]));
        exit(0);
    }
}
?>
