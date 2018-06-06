<?php
function hash_24bit($vector)
{
    /* Original 32-bit FNV-1a hash */
    $hash = hexdec(hash("fnv1a32", $vector));

    /* XOR fold to 24-bit */
    $hash = ($hash >> 24) ^ ($hash & 0xffffff);

    /* Convert to hex string */
    return sprintf("%06x", $hash);
}

function verify($vector, $hash)
{
    $result = hash_24bit($vector);
    return (hash_24bit($vector) === $hash);
}


$root = json_decode(file_get_contents('vectors.json'));

foreach ($root->vectors as $vector) {
    if (isset($vector->vector)) {
        if (!verify($vector->vector, $vector->hash)) {
            echo "Vector '{$vector->vector}' does not match hash '$vector->hash'\n";
        }
    } elseif (isset($vector->vectorHex)) {
        $str = hex2bin($vector->vectorHex);
        if (!verify($str, $vector->hash)) {
            echo "Vector '{$vector->vectorHex}' does not match hash '$vector->hash'\n";
        }
    }
}
?>
