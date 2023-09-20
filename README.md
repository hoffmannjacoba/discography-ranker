# Discography Ranker

## General Info
This project assists users with ranking an artist's discography by spliting up
the ranking process into simple song 1 or song 2 decisions.
	
## Technologies
Project is created with:

* Python version: 3.11
	
## Setup

### Install Dependencies

```
$ pip install pillow
$ pip install python-dotenv
$ pip install requests
$ pip install tk
```

### Obtain a API Key and Secret from Spotify

1. Create a new file in the same directory as ranker.py and name it .env

2. Copy and paste the following lines into your .env file
   
   ``` 
   CLIENT_ID = ""
   CLIENT_SECRET = ""
   ```
   
3. Go to https://developer.spotify.com/ and login to your Spotify account.

4. Once logged in, click on the account dropdown in top righthand corner and select "Dashboard".

5. In the Dashboard, click "Create app" and fill out the "App name", "App description", and "Redirect URI" fields.
   (For the redirect URI you can use http://localhost:3000)

6. Once you create your app, click on its name in the dashboard to open it. Then click "Settings"
   to open the Basic Information page.
  
7. Copy the "Client ID" and the "Client secret" from the Basic Information page and paste them
    into their respective spots in the .env file.

## Running the Ranker

To start the ranking process, simply run the ranker.py file.

When you run ranker.py for the first time it will generate several directories which contain
artist specific files and are updated after each program execution.

* /results
* /saves
* /backups

The results directory stores text files which display current rankings to the user.

The saves directory stores text files which store rankings for future program use. This aims to 
avoid reranking previously ranked songs when adding new songs to the ranking.

The backups directory stores is identical to the saves directory except for that it stores the previous
ranking instead of the current ranking. This aims to prevent old rankings from being accidentally lost when
they are overidden by a new ranking. To restore a lost ranking, simply copy and paste the artist's backup
file text into the artist's save file.

## Tips

* Beware that large discographies may take many hours to rank. When ranking large discographies, it may be
  less daunting to rank one or two albums at a time instead of the entire catalog at once. The rankings will
  be saved across executions as long as you check the "Include and reference previous results" checkbox
  whenever you wish to add on to the previous ranking.

* Use the skit/extra button to remove skits and other "extra" type tracks from the main ranking and negate
  their effect on the album ranking. This button only needs to clicked once per track you wish to classify
  as a skit/extra despite it appearing for every song 1 or song 2 decision. Pressing this button a second time
  will not remove the track's skit/extra classification.

* The ranking process implements a merge sort algorithm, so the amount of song 1 or song 2 decisions
  you will have to make to complete the ranking increases at a rate of n*log(n).
