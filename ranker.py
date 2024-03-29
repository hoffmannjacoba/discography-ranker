import base64
import io
import json
import os
import os.path
import PIL.Image, PIL.ImageTk
import shutil
import urllib.request
from dotenv import load_dotenv
from requests import get, post
from tkinter import *
from tkinter import ttk


class WebImage:
    def __init__(self, url):
        with urllib.request.urlopen(url) as u:
            rawData = u.read()
        image = PIL.Image.open(io.BytesIO(rawData))
        self.image = PIL.ImageTk.PhotoImage(image)

    def get(self):
        return self.image


def get_token(clientId, clientSecret):
    authString = clientId + ":" + clientSecret
    authBytes = authString.encode("utf-8")
    authBase64 = str(base64.b64encode(authBytes), "utf-8")
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + authBase64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    result = post(url, headers=headers, data=data)
    return json.loads(result.content)["access_token"]


def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


def search_for_artist(token, artistName):
    headers = get_auth_header(token)
    queryUrl = "https://api.spotify.com/v1/search" + f"?q={artistName}&type=artist&limit=1"
    result = get(queryUrl, headers=headers)
    jsonResult = json.loads(result.content)["artists"]["items"]
    if len(jsonResult) == 0:
        print("No artist with this name exists")
        return None
    return jsonResult[0]


def get_artist_discography(token, artistId):
    headers = get_auth_header(token)
    offset = 0
    while True:
        url = f"https://api.spotify.com/v1/artists/{artistId}/albums?country=US&offset={offset}&limit=50&include_groups=album,single,compilation"
        result = get(url, headers=headers)
        if offset == 0:
            jsonResult = json.loads(result.content)["items"]
        else:
            tempJsonResult = json.loads(result.content)
            if not tempJsonResult["items"]:
                break
            jsonResult += tempJsonResult["items"]
        offset += 50
    return jsonResult


def filter_duplicate_releases(token, releases):
    headers = get_auth_header(token)
    discoveredReleases = []
    filteredReleaseList = []
    for index, release in enumerate(releases):
        releaseJson = json.loads(get(release['href'], headers=headers).content)
        if index != 0:
            fetchLabel.destroy()
        fetchLabel = Label(root, text=f"Fetching releases ({releaseJson['name']})", anchor=CENTER, font="Helvetica")
        fetchLabel.pack(fill=BOTH, expand=True)
        root.update()
        if (releaseJson['name'], releaseJson['album_type']) not in discoveredReleases:
            discoveredReleases.append((releaseJson['name'], releaseJson['album_type']))
            filteredReleaseList.append(releaseJson)
        else:
            for index, discoveredRelease in enumerate(discoveredReleases):
                if discoveredRelease == (releaseJson['name'], releaseJson['album_type']):
                    if filteredReleaseList[index]['popularity'] < releaseJson['popularity']:
                        del filteredReleaseList[index]
                        filteredReleaseList.insert(index, releaseJson)
                        break
        if index == len(releases) - 1:
            fetchLabel.destroy()
    return filteredReleaseList


def get_tracks(token, albums):
    headers = get_auth_header(token)
    discoveredTracks = []
    filteredTrackList = []
    for albumIndex, album in enumerate(albums):
        simplifiedTracks = album['tracks']['items']
        for trackIndex, track in enumerate(simplifiedTracks):
            trackJson = (json.loads(get(track['href'], headers=headers).content))
            if albumIndex != 0 or trackIndex != 0:
                addingLabel.destroy()
            addingLabel = Label(root, text=f"Adding songs ({trackJson['name']})", anchor=CENTER, font="Helvetica")
            addingLabel.pack(fill=BOTH, expand=True)
            root.update()
            if track['name'] not in discoveredTracks:
                discoveredTracks.append(trackJson['name'])
                filteredTrackList.append(trackJson)
            else:
                for index, discoveredTrack in enumerate(discoveredTracks):
                    if discoveredTrack == trackJson['name']:
                        if filteredTrackList[index]['popularity'] < trackJson['popularity']:
                            del filteredTrackList[index]
                            filteredTrackList.insert(index, trackJson)
                            break
            if albumIndex == len(albums) - 1 and trackIndex == len(simplifiedTracks) - 1:
                addingLabel.destroy()
    return filteredTrackList


def rank_tracks_util(savedDisc, disc):
    rankedDisc = [] # [[Name, Album, Cover Art Url, Popularity, Year, Month, Day], ...]
    left = savedDisc
    right = disc

    # remove previously ranked tracks
    for li, rankedTrack in enumerate(left):
        for ri, unrankedTrack in enumerate(right):
            if rankedTrack[0] == unrankedTrack[0]:
                if rankedTrack[1] == '*Single/EP*' and unrankedTrack[1] != '*Single/EP*': # prefer album version > single version
                    left[li] = unrankedTrack
                elif rankedTrack[3] < unrankedTrack[3]: # prefer more popular version > less popular version
                    left[li] = unrankedTrack
                del right[ri]
                break
    
    rank_tracks(right)
    i = 0  # left index
    j = 0  # right index
    while i < len(left) and j < len(right):
        global leftName
        leftName = f"{left[i][0]}"
        global rightName
        rightName = f"{right[j][0]}"
        if len(leftName) > 35:
            leftName = leftName[0:35] + "..."
        if len(rightName) > 35:
            rightName = rightName[0:35] + "..."

        leftLabel = Label(rankerFrame, text=leftName, font=("Helvetica", 20))
        rightLabel = Label(rankerFrame, text=rightName, font=("Helvetica", 20))
        leftImage = WebImage(left[i][2]).get()
        leftImageLabel = Label(rankerFrame, image=leftImage)
        rightImage = WebImage(right[j][2]).get()
        rightImageLabel = Label(rankerFrame, image=rightImage)
        leftButton = Button(rankerFrame, text=leftName, command=left_song_chosen, font="Helvetica")
        rightButton = Button(rankerFrame, text=rightName, command=right_song_chosen, font="Helvetica")
        leftSkitButton = Button(rankerFrame, text="Skit/Extra", command=left_song_skit, font="Helvetica")
        rightSkitButton = Button(rankerFrame, text="Skit/Extra", command=right_song_skit, font="Helvetica")
        skitButtonsLabel = Label(rankerFrame, text="Clicking the Skit/Extra buttons will negate the track's effect on the album ranking", font="Helvetica")
        leftLabel.grid(row=0, column=0)
        rightLabel.grid(row=0, column=3)
        leftImageLabel.grid(row=1, column=0)
        leftButton.grid(row=1, column=1)
        rightButton.grid(row=1, column=2)
        rightImageLabel.grid(row=1, column=3)
        leftSkitButton.grid(row=2, column=0)
        rightSkitButton.grid(row=2, column=3)
        skitButtonsLabel.grid(row=2, column=1, columnspan=2)
        leftButton.wait_variable(songChosen)
        songChosen.set(0)

        if betterTrack == 1:
            rankedDisc.append(left[i])
            i += 1
        else:
            rankedDisc.append(right[j])
            j += 1

        leftLabel.destroy()
        rightLabel.destroy()
        leftImageLabel.destroy()
        rightImageLabel.destroy()
        leftButton.destroy()
        rightButton.destroy()
        leftSkitButton.destroy()
        rightSkitButton.destroy()
        skitButtonsLabel.destroy()
 
    while i < len(left):
        rankedDisc.append(left[i])
        i += 1
    while j < len(right):
        rankedDisc.append(right[j])
        j += 1
    return rankedDisc


def rank_tracks(disc):
    if len(disc) > 1:
        left = disc[:len(disc)//2]
        right = disc[len(disc)//2:]
        rank_tracks(left)
        rank_tracks(right)
        i = 0  # left index
        j = 0  # right index
        k = 0  # merged index
        while i < len(left) and j < len(right):
            global leftName
            leftName = f"{left[i][0]}"
            global rightName
            rightName = f"{right[j][0]}"
            if len(leftName) > 35:
                leftName = leftName[0:35] + "..."
            if len(rightName) > 35:
                rightName = rightName[0:35] + "..."

            leftLabel = Label(rankerFrame, text=leftName, font=("Helvetica", 20))
            rightLabel = Label(rankerFrame, text=rightName, font=("Helvetica", 20))
            leftImage = WebImage(left[i][2]).get()
            leftImageLabel = Label(rankerFrame, image=leftImage)
            rightImage = WebImage(right[j][2]).get()
            rightImageLabel = Label(rankerFrame, image=rightImage)
            leftButton = Button(rankerFrame, text=leftName, command=left_song_chosen, font="Helvetica", width=30)
            rightButton = Button(rankerFrame, text=rightName, command=right_song_chosen, font="Helvetica", width=30)
            leftSkitButton = Button(rankerFrame, text="Skit/Extra", command=left_song_skit, font="Helvetica")
            rightSkitButton = Button(rankerFrame, text="Skit/Extra", command=right_song_skit, font="Helvetica")
            skitButtonsLabel = Label(rankerFrame, text="The Skit/Extra button will prevent the track from being considered in the album ranking calculation", font="Helvetica")
            leftLabel.grid(row=0, column=0)
            rightLabel.grid(row=0, column=3)
            leftImageLabel.grid(row=1, column=0)
            leftButton.grid(row=1, column=1)
            rightButton.grid(row=1, column=2)
            rightImageLabel.grid(row=1, column=3)
            leftSkitButton.grid(row=2, column=0)
            rightSkitButton.grid(row=2, column=3)
            skitButtonsLabel.grid(row=2, column=1, columnspan=2)
            leftButton.wait_variable(songChosen)
            songChosen.set(0)

            if betterTrack == 1:
                disc[k] = left[i]
                i += 1
                k += 1
            else:
                disc[k] = right[j]
                j += 1
                k += 1

            leftLabel.destroy()
            rightLabel.destroy()
            leftImageLabel.destroy()
            rightImageLabel.destroy()
            leftButton.destroy()
            rightButton.destroy()
            leftSkitButton.destroy()
            rightSkitButton.destroy()
            skitButtonsLabel.destroy()

        while i < len(left):
            disc[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            disc[k] = right[j]
            j += 1
            k += 1


def sort_albums_by_year(albums):
    if len(albums) > 1:
        left = albums[:len(albums)//2]
        right = albums[len(albums)//2:]
        sort_albums_by_year(left)
        sort_albums_by_year(right)
        i = 0  # left index
        j = 0  # right index
        k = 0  # merged index
        while i < len(left) and j < len(right):
            if (left[i][1] > right[j][1]):
                albums[k] = left[i]
                i += 1
                k += 1
            else:
                albums[k] = right[j]
                j += 1
                k += 1
        while i < len(left):
            albums[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            albums[k] = right[j]
            j += 1
            k += 1



def sort_albums_by_votes(albums):
    if len(albums) > 1:
        left = albums[:len(albums)//2]
        right = albums[len(albums)//2:]
        sort_albums_by_votes(left)
        sort_albums_by_votes(right)
        i = 0  # left index
        j = 0  # right index
        k = 0  # merged index
        while i < len(left) and j < len(right):
            if (left[i][1] < right[j][1]):
                albums[k] = left[i]
                i += 1
                k += 1
            else:
                albums[k] = right[j]
                j += 1
                k += 1
        while i < len(left):
            albums[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            albums[k] = right[j]
            j += 1
            k += 1


def fill_artist():
    if textEntry.get().replace(" ", "") != "":
        global userSelectedArtist
        userSelectedArtist = search_for_artist(token, textEntry.get())
        artistSet.set(1)


def save_selected_releases():
    global userFilteredReleaseList
    userFilteredReleaseList = []
    for index in range(len(filteredReleaseList)):
        if intVarList[index].get():
            userFilteredReleaseList.append(filteredReleaseList[index])
    if len(userFilteredReleaseList) > 0:
        releasesSelected.set(1)


def left_song_chosen():
    global betterTrack
    betterTrack = 1
    songChosen.set(1)


def right_song_chosen():
    global betterTrack
    betterTrack = 2
    songChosen.set(1)

def left_song_skit():
    if leftName not in skits:
        skits.append(leftName)

def right_song_skit():
    if rightName not in skits:
        skits.append(rightName)

load_dotenv()
token = get_token(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
root = Tk()
root.title("Discography Ranker")
root.geometry("1300x700")
abspath = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(f'{abspath}/backupSaves'):
    os.mkdir(f'{abspath}/backupSaves')
if not os.path.exists(f'{abspath}/results'):
    os.mkdir(f'{abspath}/results')
if not os.path.exists(f'{abspath}/saves'):
    os.mkdir(f'{abspath}/saves')

# populate discography.txt with a discography of the users choice
enterArtistLabel = Label(root, text="Who's discography would you like to rank?", font=("Helvetica", 30))
textEntry = Entry(root, width=25, font=("Helvetica", 18))
artistSet = IntVar()
enterButton = Button(root, text="Search", command=fill_artist, font="Helvetica")
enterArtistLabel.pack(pady=(275,5))
textEntry.pack()
enterButton.pack()
enterButton.wait_variable(artistSet)
enterArtistLabel.destroy()
textEntry.destroy()
enterButton.destroy()

artistName = userSelectedArtist["name"].replace(" ", "")
filteredReleaseList = filter_duplicate_releases(token, get_artist_discography(token, userSelectedArtist["id"]))
longestReleaseNameLength = 0
for index, release in enumerate(filteredReleaseList):
    if len(release['name']) > longestReleaseNameLength:
        longestReleaseNameLength = len(release['name'])

loadingLabel = Label(root, text="loading...", anchor=CENTER, font="Helvetica")
loadingLabel.pack(fill=BOTH, expand=True)
root.update()
releasesLabel = Label(root, text="Check all of the releases you would like to include in the ranking, then click rank", font=("Helvetica", 24))
releaseListMainFrame = Frame(root, highlightbackground='#1DB954', highlightthickness=2, width=7*longestReleaseNameLength+305, height=400)
releaseListCanvas = Canvas(releaseListMainFrame)
releaseListCanvas.pack(side=LEFT, fill=BOTH, expand=1)
releaseListScrollbar = ttk.Scrollbar(releaseListMainFrame, orient=VERTICAL, command=releaseListCanvas.yview)
releaseListScrollbar.pack(side=RIGHT, fill=Y)
releaseListCanvas.configure(yscrollcommand=releaseListScrollbar.set)
releaseListCanvas.bind('<Configure>', lambda e: releaseListCanvas.configure(scrollregion=releaseListCanvas.bbox("all")))
releaseListScrollableFrame = Frame(releaseListCanvas)
releaseListCanvas.create_window((0,0), window=releaseListScrollableFrame, anchor="nw")
albumCoverList = []
albumCoverLabelList = []
intVarList = []
checkButtonList = []
longestReleaseNameLength = ""
for index, release in enumerate(filteredReleaseList):
    albumCoverList.append(WebImage(release['images'][2]['url']).get())
    albumCoverLabelList.append(Label(releaseListScrollableFrame, image=albumCoverList[index], width=70, anchor="w"))
    intVarList.append(IntVar())
    if release['album_type'] == "album":
        checkButtonText = f"{release['name']} (Album, {release['total_tracks']} tracks)"
    elif release['album_type'] == "compilation":
        checkButtonText = f"{release['name']} (Compilation, {release['total_tracks']} tracks)"
    elif release['total_tracks'] == 1:
        checkButtonText = f"{release['name']} (Single/EP, {release['total_tracks']} track)"
    else:
        checkButtonText = f"{release['name']} (Single/EP, {release['total_tracks']} tracks)"
    checkButtonList.append(Checkbutton(releaseListScrollableFrame, text=checkButtonText, width=+200, variable=intVarList[index], anchor="w", font="Helvetica"))
useOldRanking = IntVar()
oldRankingCheckButton = Checkbutton(root, text="Include and reference previous results. Previous results for this artist will be lost if left unchecked.", variable=useOldRanking, font=("Helvetica", 18))
oldRankingCheckButtonLabel = Label(root, text="(To restore a lost ranking, copy and paste the artist's backup file into their save file.)", font="Helvetica")
rankButton = Button(root, text="Rank", command=save_selected_releases, font="Helvetica")
loadingLabel.destroy()

releasesLabel.pack(pady=(100, 15))
releaseListMainFrame.pack_propagate(0)
releaseListMainFrame.pack()
for index, albumCoverLabel in enumerate(albumCoverLabelList):
    albumCoverLabel.grid(row=index, column=0)
for index, checkButton in enumerate(checkButtonList):
    checkButton.grid(row=index, column=1)
oldRankingCheckButton.pack(pady=(15, 0))
oldRankingCheckButtonLabel.pack()
rankButton.pack()
releasesSelected = IntVar()
rankButton.wait_variable(releasesSelected)
releasesLabel.destroy()
releaseListMainFrame.destroy()
oldRankingCheckButton.destroy()
oldRankingCheckButtonLabel.destroy()
rankButton.destroy()

tracklist = get_tracks(token, userFilteredReleaseList)
rstring = ""
for track in tracklist:
    if track['album']['album_type'] == "album":
        rstring += f"{track['name']}|| {track['album']['name']}|| {track['album']['images'][1]['url']}|| {track['popularity']}|| song|| {track['album']['release_date']}\n"
    elif track['album']['album_type'] == "single":
        rstring += f"{track['name']}|| *Single/EP*|| {track['album']['images'][1]['url']}|| {track['popularity']}|| song|| {track['album']['release_date']}\n"
    else:
        rstring += f"{track['name']}|| *Compilation*|| {track['album']['images'][1]['url']}|| {track['popularity']}|| song|| {track['album']['release_date']}\n"
with open(f'{abspath}/discography.txt', 'w') as results:
    results.write(rstring)

# populate discography and albums
discography = []    # [[Song, Album, Cover Art Url, Popularity, Skit, Year, Month, Day], [Song, Album, Cover Art Url, Popularity, Skit, Year, Month, Day, Popularity]...]
albums = []         # [[Album, Year, Month, Day], [Album, Year, Month, Day]...]
with open(f'{abspath}/discography.txt', 'r') as tracks:
    for track in tracks:
        track = track[:-1]
        metadata = track.split('|| ')
        date = metadata[5].split('-')
        metadata[5] = date[0]       # year
        metadata.append(date[1])    # month
        metadata.append(date[2])    # day
        discography.append(metadata)
        if metadata[1] != "*Single/EP*" and [metadata[1], metadata[5], metadata[6], metadata[7]] not in albums:
            albums.append([metadata[1], metadata[5], metadata[6], metadata[7]])
os.remove(f'{abspath}/discography.txt')
sort_albums_by_year(albums)

# rank discography
rankerFrame = Frame(root)
rankerFrame.pack(fill=BOTH, expand=True, anchor=CENTER)
rankerFrame.grid_columnconfigure((0,3), weight=1)
rankerFrame.grid_rowconfigure((0,2), weight=1)
songChosen = IntVar()
rankedDiscography = []  # [[Song, Album, Cover Art Url, Popularity, Skit, Year, Month, Day], [Song, Album, Cover Art Url, Popularity, Skit, Year, Month, Day, Popularity]...]
skits = []
if useOldRanking.get() and os.path.isfile(f'{abspath}/saves/{artistName}Save.txt'):
    with open(f'{abspath}/saves/{artistName}Save.txt', 'r') as rankedTracks:
        for track in rankedTracks:
            track = track[:-1]
            metadata = track.split('|| ')
            rankedDiscography.append(metadata)
            if metadata[1] != "*Single/EP*" and [metadata[1], metadata[5], metadata[6], metadata[7]] not in albums:
                albums.append([metadata[1], metadata[5], metadata[6], metadata[7]])
            if metadata[4] == "skit":
                skits.append(metadata[0])
    discography = rank_tracks_util(rankedDiscography, discography)
    sort_albums_by_year(albums)
else:
    rank_tracks(discography)
rankerFrame.destroy()

# conclude album ranking
albumVotes = albums.copy()
for album in albumVotes:
    album[1] = 0
    numTracks = 0
    for ranking, track in enumerate(discography):
        if track[1] == album[0] and track[0] not in skits:
            album[1] += ranking + 1
            numTracks += 1
    album[1] /= numTracks
sort_albums_by_votes(albumVotes)

# print results and save in results.txt
rstring = "Your Discography Ranking\n"
sstring = ""
offset = 1
for ranking, track in enumerate(discography):
    if track[0] in skits:
        offset -= 1
        sstring += f"{track[0]}|| {track[1]}|| {track[2]}|| {track[3]}|| skit|| {track[5]}|| {track[6]}|| {track[7]}\n"
    else:
        rstring += f"    {ranking + offset}. {track[0]}\n"
        sstring += f"{track[0]}|| {track[1]}|| {track[2]}|| {track[3]}|| song|| {track[5]}|| {track[6]}|| {track[7]}\n"
        track[7] = ranking + offset
rstring += "\nYour Album Ranking\n"
for ranking, album in enumerate(albumVotes):
    rstring += f"    {ranking + 1}.  {album[0]}\n"
rstring += "\nAlbum Breakdown\n"
for album in albums:
    rstring += f"\n    {album[0]}\n"
    i = 1
    for track in discography:
        if (track[1] == album[0]):
            rstring += f"        {i}. {track[0]}"
            if track[0] in skits:
                rstring += " (Skit/Extra)"
            else:
                rstring += f"  ({track[7]})"
            rstring += "\n"
            i += 1
rstring += "\n    Other Releases\n"
i = 1
for ranking, track in enumerate(discography):
    if track[1] == "*Single/EP*":
        rstring += f"        {i}. {track[0]} ({ranking + 1})\n"
        i += 1
if os.path.isfile(f'{abspath}/saves/{artistName}Save.txt'):
    shutil.copyfile(f'{abspath}/saves/{artistName}Save.txt', f'{abspath}/backupSaves/{artistName}SaveBackup.txt')
with open(f'{abspath}/results/{artistName}Results.txt', 'w') as results:
    results.write(rstring)
with open(f'{abspath}/saves/{artistName}Save.txt', 'w') as rankedDiscography:
    rankedDiscography.write(sstring)

resultLabel = Label(root, text=f"Your ranking is complete!\nCheck it out at results/{artistName}Results.txt", font="Helvetica")
quitButton = Button(root, text="Exit", command=root.quit, font="Helvetica")
resultLabel.pack(pady=(300,0))
quitButton.pack()

root.mainloop()