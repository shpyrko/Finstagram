#######################IMPORTANT##########################

# THIS IS JUST A TEMPLATE
# It won't work completely by taking this template, this
#   is meant to help you get start if you choose to
#   store your photos using BLOB.
# I tried my best to provide you with example code that
#   reflects the finstagram schema we are using.

# For further information refer to this link
# https://pynative.com/python-mysql-blob-insert-retrieve-file-image-as-a-blob-in-mysql/

#######################IMPORTANT##########################

import pymysql.cursors

#####################################################
# Inserting Images as BLOB data into MySQL Table
#####################################################

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

def insertBLOB(photo, allFollowers, caption, username):
    print("Inserting BLOB into photo table")

    #   Just to clarify since you specify that the table auto increments photoIDs
    #   You do not havy to insert into that column since that will be done for you.

    try:
        connection = pymysql.connect(host='localhost',
                               port=8889,
                               user='root',
                               password='root',
                               db='finstagram',
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)

        cursor = connection.cursor()
        sql_insert_blob_query = """ INSERT INTO Photo
                          (postingDate, filePath, allFollowers, caption, poster) VALUES (current_timestamp,%s,%s,%s,%s)"""

        photo = convertToBinaryData(photo)

        # Convert data into tuple format
        insert_blob_tuple = (photo, allFollowers, caption, username)
        result = cursor.execute(sql_insert_blob_query, insert_blob_tuple)
        connection.commit()
        print("Image and file inserted successfully as a BLOB into Photos table", result)

    finally:
        cursor.close()
        connection.close()
        print("MySQL connection is closed")

################################################################
# Retrieving Image and File stored as a BLOB from MySQL Table
################################################################

def write_file(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)

def readBLOB(photo_id):
    print("Reading BLOB data from Photo table")

    try:
        connection = pymysql.connect(host='localhost',
                               port=8889,
                               user='root',
                               password='root',
                               db='finstagram',
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)

        cursor = connection.cursor()
        sql_fetch_blob_query = """SELECT photo from Photo where pID = %s"""

        cursor.execute(sql_fetch_blob_query, photo_id)
        record = cursor.fetchall()
        for row in record:
            print("photoID = ", row[0])
            image = row[1]
            print("Storing photo on disk \n")
            write_file(image, "newPhoto")

    finally:
        cursor.close()
        connection.close()
        print("MySQL connection is closed")
