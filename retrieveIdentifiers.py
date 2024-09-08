import csv
import json
import pathlib
import urllib.parse
import urllib.request
import warnings


def get_first_artist(artist):
    delimiters = [",", "&", "and", "feat", "ft", "featuring"]

    for delimiter in delimiters:
        artist = " ".join(artist.split(delimiter))

    return artist.split()[0]


def get_title_words(title):
    delimiters = [",", "[", "]", "(", ")", "feat.", "ft.", "remix", "mix"]

    title_new = title.lower()
    for delimiter in delimiters:
        title_new = " ".join(title_new.split(delimiter))

    return [w for w in title_new.split() if len(w) > 1]


def retrieve_itunes_identifier(title, artist):
    headers = {
        "X-Apple-Store-Front": "143446-10,32 ab:rSwnYxS0 t:music2",
        "X-Apple-Tz": "7200",
    }
    url = (
        "https://itunes.apple.com/WebObjects/MZStore.woa/wa/search?clientApplication=MusicPlayer&term="
        + urllib.parse.quote(title)
    )
    request = urllib.request.Request(url, None, headers)

    try:
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode("utf-8"))
        songs = [
            result
            for result in data["storePlatformData"]["lockup"]["results"].values()
            if result["kind"] == "song"
        ]

        # Attempt to match by title & artist
        for song in songs:
            if song["name"].lower() == title.lower() and (
                song["artistName"].lower() in artist.lower()
                or artist.lower() in song["artistName"].lower()
            ):
                return song["id"], title, song["artistName"]

        for song in songs:
            first_artist_orig = get_first_artist(artist.lower().strip())
            first_artist_itunes = get_first_artist(song["artistName"].lower().strip())
            if (
                first_artist_orig in song["artistName"].lower()
                or first_artist_itunes in artist.lower()
            ):
                orig_words = get_title_words(title.lower().strip())

                candidate_words = get_title_words(song["name"].lower().strip())

                title_words_the_same = [
                    part
                    for part in candidate_words
                    if part
                    and (part in orig_words or any(part in w for w in orig_words))
                ]

                if (
                    len(orig_words) > 4
                    and len(title_words_the_same) >= len(orig_words) - 1
                ) or len(orig_words) == len(title_words_the_same):
                    warnings.warn(
                        "Title and artist match not found, but title is similar to the original"
                    )

                    return song["id"], title, song["artistName"]

        return None, None, None
    except Exception as e:
        # We don't do any fancy error handling.. Just return None if something went wrong
        print(e)
        return None, None, None


parent = pathlib.Path("_spotify")

new_parent = pathlib.Path("_itunes")
new_parent.mkdir(exist_ok=True)

for f in parent.iterdir():
    if f.is_dir() or f.suffix != ".csv":
        continue

    itunes_identifiers = []
    with open(f, encoding="utf-8") as playlist_file:
        playlist_reader = csv.reader(playlist_file)
        next(playlist_reader)

        for row in playlist_reader:
            title, artist = row[1], row[3]
            itunes_identifier, itunes_title, itunes_artist = retrieve_itunes_identifier(
                title, artist
            )

            if itunes_identifier:
                itunes_identifiers.append(itunes_identifier)
                print(
                    "{} - {} => {} [{} - {}]".format(
                        title, artist, itunes_identifier, itunes_title, itunes_artist
                    )
                )
            else:
                noresult = "{} - {} => Not Found".format(title, artist)
                print(noresult)
                with open("noresult.txt", "a+", encoding="utf-8") as f:
                    f.write(noresult)
                    f.write("\n")

    with open(new_parent / f.name, "w", encoding="utf-8") as output_file:
        for itunes_identifier in itunes_identifiers:
            output_file.write(str(itunes_identifier) + "\n")

# Improved by @piotrgredowski on GitHub
# Developped by @therealmarius on GitHub
# Based on the work of @simonschellaert on GitHub
# Github project page: https://github.com/therealmarius/Spotify-2-AppleMusic
