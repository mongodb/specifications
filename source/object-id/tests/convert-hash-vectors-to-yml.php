<?php
function echoYaml($vector, $hash)
{
    $type = 'vector';

    if (preg_replace('/[\x00-\x1f\x7f-\xff]/', "", $vector) !== $vector)
    {
        $type = 'vectorHex';
        $vector = bin2hex($vector);
    }
    printf( <<<TEMPLATE
  {
    $type: '$vector',
    hash: "$hash",
  },

TEMPLATE
    , $type, $vector, $hash);
}

function hash_24bit($vector)
{
    $hash = hexdec(hash("fnv1a32", $vector));
    $hash = ($hash >> 24) ^ ($hash & 0xffffff);
    return sprintf("%06x", $hash);
}

function TEST($vector)
{
    echoYaml($vector, hash_24bit($vector));
}

function TEST0($vector)
{
    $vector .= "\0";
    echoYaml($vector, hash_24bit($vector));
}

function R10($input)
{
    return str_repeat($input, 10);
}

function R500($input)
{
    return str_repeat($input, 500);
}

echo "vectors: [\n";

TEST("");
TEST("a");
TEST("b");
TEST("c");
TEST("d");
TEST("e");
TEST("f");
TEST("fo");
TEST("foo");
TEST("foob");
TEST("fooba");
TEST("foobar");
TEST0("");
TEST0("a");
TEST0("b");
TEST0("c");
TEST0("d");
TEST0("e");
TEST0("f");
TEST0("fo");
TEST0("foo");
TEST0("foob");
TEST0("fooba");
TEST0("foobar");
TEST("ch");
TEST("cho");
TEST("chon");
TEST("chong");
TEST("chongo");
TEST("chongo ");
TEST("chongo w");
TEST("chongo wa");
TEST("chongo was");
TEST("chongo was ");
TEST("chongo was h");
TEST("chongo was he");
TEST("chongo was her");
TEST("chongo was here");
TEST("chongo was here!");
TEST("chongo was here!\n");
TEST0("ch");
TEST0("cho");
TEST0("chon");
TEST0("chong");
TEST0("chongo");
TEST0("chongo ");
TEST0("chongo w");
TEST0("chongo wa");
TEST0("chongo was");
TEST0("chongo was ");
TEST0("chongo was h");
TEST0("chongo was he");
TEST0("chongo was her");
TEST0("chongo was here");
TEST0("chongo was here!");
TEST0("chongo was here!\n");
TEST("cu");
TEST("cur");
TEST("curd");
TEST("curds");
TEST("curds ");
TEST("curds a");
TEST("curds an");
TEST("curds and");
TEST("curds and ");
TEST("curds and w");
TEST("curds and wh");
TEST("curds and whe");
TEST("curds and whey");
TEST("curds and whey\n");
TEST0("cu");
TEST0("cur");
TEST0("curd");
TEST0("curds");
TEST0("curds ");
TEST0("curds a");
TEST0("curds an");
TEST0("curds and");
TEST0("curds and ");
TEST0("curds and w");
TEST0("curds and wh");
TEST0("curds and whe");
TEST0("curds and whey");
TEST0("curds and whey\n");
TEST("hi");
TEST0("hi");
TEST("hello");
TEST0("hello");
TEST("\xff\x00\x00\x01");
TEST("\x01\x00\x00\xff");
TEST("\xff\x00\x00\x02");
TEST("\x02\x00\x00\xff");
TEST("\xff\x00\x00\x03");
TEST("\x03\x00\x00\xff");
TEST("\xff\x00\x00\x04");
TEST("\x04\x00\x00\xff");
TEST("\x40\x51\x4e\x44");
TEST("\x44\x4e\x51\x40");
TEST("\x40\x51\x4e\x4a");
TEST("\x4a\x4e\x51\x40");
TEST("\x40\x51\x4e\x54");
TEST("\x54\x4e\x51\x40");
TEST("127.0.0.1");
TEST0("127.0.0.1");
TEST("127.0.0.2");
TEST0("127.0.0.2");
TEST("127.0.0.3");
TEST0("127.0.0.3");
TEST("64.81.78.68");
TEST0("64.81.78.68");
TEST("64.81.78.74");
TEST0("64.81.78.74");
TEST("64.81.78.84");
TEST0("64.81.78.84");
TEST("feedface");
TEST0("feedface");
TEST("feedfacedaffdeed");
TEST0("feedfacedaffdeed");
TEST("feedfacedeadbeef");
TEST0("feedfacedeadbeef");
TEST("line 1\nline 2\nline 3");
TEST("chongo <Landon Curt Noll> /\\../\\");
TEST0("chongo <Landon Curt Noll> /\\../\\");
TEST("chongo (Landon Curt Noll) /\\../\\");
TEST0("chongo (Landon Curt Noll) /\\../\\");
TEST("http://antwrp.gsfc.nasa.gov/apod/astropix.html");
TEST("http://en.wikipedia.org/wiki/Fowler_Noll_Vo_hash");
TEST("http://epod.usra.edu/");
TEST("http://exoplanet.eu/");
TEST("http://hvo.wr.usgs.gov/cam3/");
TEST("http://hvo.wr.usgs.gov/cams/HMcam/");
TEST("http://hvo.wr.usgs.gov/kilauea/update/deformation.html");
TEST("http://hvo.wr.usgs.gov/kilauea/update/images.html");
TEST("http://hvo.wr.usgs.gov/kilauea/update/maps.html");
TEST("http://hvo.wr.usgs.gov/volcanowatch/current_issue.html");
TEST("http://neo.jpl.nasa.gov/risk/");
TEST("http://norvig.com/21-days.html");
TEST("http://primes.utm.edu/curios/home.php");
TEST("http://slashdot.org/");
TEST("http://tux.wr.usgs.gov/Maps/155.25-19.5.html");
TEST("http://volcano.wr.usgs.gov/kilaueastatus.php");
TEST("http://www.avo.alaska.edu/activity/Redoubt.php");
TEST("http://www.dilbert.com/fast/");
TEST("http://www.fourmilab.ch/gravitation/orbits/");
TEST("http://www.fpoa.net/");
TEST("http://www.ioccc.org/index.html");
TEST("http://www.isthe.com/cgi-bin/number.cgi");
TEST("http://www.isthe.com/chongo/bio.html");
TEST("http://www.isthe.com/chongo/index.html");
TEST("http://www.isthe.com/chongo/src/calc/lucas-calc");
TEST("http://www.isthe.com/chongo/tech/astro/venus2004.html");
TEST("http://www.isthe.com/chongo/tech/astro/vita.html");
TEST("http://www.isthe.com/chongo/tech/comp/c/expert.html");
TEST("http://www.isthe.com/chongo/tech/comp/calc/index.html");
TEST("http://www.isthe.com/chongo/tech/comp/fnv/index.html");
TEST("http://www.isthe.com/chongo/tech/math/number/howhigh.html");
TEST("http://www.isthe.com/chongo/tech/math/number/number.html");
TEST("http://www.isthe.com/chongo/tech/math/prime/mersenne.html");
TEST("http://www.isthe.com/chongo/tech/math/prime/mersenne.html#largest");
TEST("http://www.lavarnd.org/cgi-bin/corpspeak.cgi");
TEST("http://www.lavarnd.org/cgi-bin/haiku.cgi");
TEST("http://www.lavarnd.org/cgi-bin/rand-none.cgi");
TEST("http://www.lavarnd.org/cgi-bin/randdist.cgi");
TEST("http://www.lavarnd.org/index.html");
TEST("http://www.lavarnd.org/what/nist-test.html");
TEST("http://www.macosxhints.com/");
TEST("http://www.mellis.com/");
TEST("http://www.nature.nps.gov/air/webcams/parks/havoso2alert/havoalert.cfm");
TEST("http://www.nature.nps.gov/air/webcams/parks/havoso2alert/timelines_24.cfm");
TEST("http://www.paulnoll.com/");
TEST("http://www.pepysdiary.com/");
TEST("http://www.sciencenews.org/index/home/activity/view");
TEST("http://www.skyandtelescope.com/");
TEST("http://www.sput.nl/~rob/sirius.html");
TEST("http://www.systemexperts.com/");
TEST("http://www.tq-international.com/phpBB3/index.php");
TEST("http://www.travelquesttours.com/index.htm");
TEST("http://www.wunderground.com/global/stations/89606.html");
TEST(R10("21701"));
TEST(R10("M21701"));
TEST(R10("2^21701-1"));
TEST(R10("\x54\xc5"));
TEST(R10("\xc5\x54"));
TEST(R10("23209"));
TEST(R10("M23209"));
TEST(R10("2^23209-1"));
TEST(R10("\x5a\xa9"));
TEST(R10("\xa9\x5a"));
TEST(R10("391581216093"));
TEST(R10("391581*2^216093-1"));
TEST(R10("\x05\xf9\x9d\x03\x4c\x81"));
TEST(R10("FEDCBA9876543210"));
TEST(R10("\xfe\xdc\xba\x98\x76\x54\x32\x10"));
TEST(R10("EFCDAB8967452301"));
TEST(R10("\xef\xcd\xab\x89\x67\x45\x23\x01"));
TEST(R10("0123456789ABCDEF"));
TEST(R10("\x01\x23\x45\x67\x89\xab\xcd\xef"));
TEST(R10("1032547698BADCFE"));
TEST(R10("\x10\x32\x54\x76\x98\xba\xdc\xfe"));
TEST(R500("\x00"));
TEST(R500("\x07"));
TEST(R500("~"));
TEST(R500("\x7f"));

echo "]\n";
?>
