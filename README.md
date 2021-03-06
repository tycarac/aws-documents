# AWS-Documents

## Introduction
Downloads AWS documents, currently whitepapers, from AWS documentation website.

## Usage

Requires Python 3.8.x and libraries:
- urllib3
- python-dateutil
- pytz
- tzlocal

Windows shell script **install-python-packages.cmd** creates virtual **venv** environment and installs packages from **requirements.txt**.

Run by activating venv environment and running module whitepapers as follows:

`.env\scripts\activate` 
`python whitepapers`

## Processing
### Determining if whitepaper to be re-downloaded
 - AWS data feed:
   - Has four date/datetime fields: dateCreated, updatedDate, datePublished, sortDate
   - dateCreated and dateUpdated are somehow related to data processing and not the whitepaper
   - datePublished has not always updated to the most current published version
   - dateSort is used to order the whitepapers on the AWS whitepapers page
 - PDF files:
     - Do not contain date related metadata (may be available in custom fields at author's discretion)

Thus dateSort is used for the date to test if a cached whitepaper is "old" and should be re-downloaded.  It is also used to build the whitepaper file name.


