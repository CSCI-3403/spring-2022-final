CSCI 3403 Final
===============

This is the final exam for CSCI 3403, Intro to Cybersecurity. It is a hands-on capture-the-flag challenge focused on web security.

How to run
----------

1. Install Python3 (tested with 3.10, but 3.7+ should work)
2. Install required Python libraries with `python3 -m pip install -r requirements.txt`
3. (Optional) Install Firefox and geckodriver from https://github.com/mozilla/geckodriver/releases. This is only required for the final XSS question.
4. Create a "secrets.json" file in the assignment server directory, which contains the server secret key, and a `dbs` folder if there is not one already.
5. Start each of the three servers with `python app.py`. The score server must be started before the assignment server. The support server is only required for the final XSS question.

Design
------

The final is made up of three services:

**Assignment server**: The assignment server is the main page users will access and hack into. It's a pretty straightforward Flask webserver, with one exception: it creates a new SQLite database for every new user, so that students cannot pollute or attack each other. These databases are stored in the `dbs` folder, and it switches databases dynamically on each request.

**Score server**: The score server handles goals, scores, and logging. It is separate from the assignment server so that students cannot somehow corrupt the data there.

**Support server**: Finally, the support server runs a small pool of Selenium Firefox webdrivers. It's one and only endpoint simply listens for a link, and visits it. This enables the support chat feature, which requires students to send links to "support staff" who will click them and trigger XSS attacks. These requests are made as the "support" account, but the student account who made the request is passed as an HTTP header and the assignment server uses that to select the correct database for that student.