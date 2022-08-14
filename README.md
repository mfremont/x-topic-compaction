# Pulsar Topic Compaction Example

## Sample time series

### `metar_ts.json`

- [METAR](https://en.wikipedia.org/wiki/METAR) observations covering 72 hours for 
  several stations in New England
- fetched from [Aviation Weather Center Text Data Server (TDS)](https://www.aviationweather.gov/dataserver)
- sorted by `observation_time`
- exported as an array of JSON objects, with one object per observation

In the US, routine observations are reported hourly, approximately 10 minutes before the
top of the hour. SPECI observations are off-schedule reports made when changes in
conditions are significant for aviation safety, and COR are corrections by a human 
observer.

Stations in the sample:
- KACK - Nantucket Memorial Airport, Nantucket, MA
- KBHB - Hancock County Airport, Bar Harbor, ME
- KBOS - Logan Airport, Boston, MA
- KCQX - Chatham Municipal Airport, Chatham, MA
- KMWN - Mount Washington Observatory, NH

## Getting started

### Prerequisites

- Docker desktop
- Python >= 3.8

### Start a standalone Pulsar

From the project root:

```shell
docker compose up -d
```

The first time you run this command for this project, Docker will download any container
images that are not cached on your system.

Eventually, you should a pair of messages like this:

```
[+] Running 1/1
 ⠿ Container pulsar-standalone-broker-1  Started 
```

### Setup to run Python clients in host OS

If you are working on Linux or macOS prior to 12.5 (Monterey), you should be able to run
the Python code directly with Python 3.8 or newer.

It is generally a good idea to create a virtual environment (venv) for experimentation.
Install the project requirements in the venv (starting from the project root):

```shell
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

After `pip` completes downloading and installing the dependency graph of `pulsar-client`,
verify that the pulsar client lib can be imported successfully:

```
python
>>> import pulsar
>>>
```

If, instead, you see an error something like

```
ImportError: dlopen(<snip>/topic-compaction/venv/lib/python3.10/site-packages/_pulsar.cpython-310-darwin.so, 0x0002): symbol not found in flat namespace (__ZN5boost6python6detail13current_scopeE)
```

then the pulsar client is not linked correctly, but you can use an interactive shell in
the broker container to run the project Python scripts.

### Start an interactive shell in the broker container

An interactive shell in the container provides a convenient way to run `pulsar-admin`
commands. 

It is also an alternative for running the project Python scripts because the container
has Python 3 with `pulsar-client` installed. The project `compose.yaml` file configures
the container to mount the project root directory as `/home`. This makes it possible to 
edit using your favorite editor/IDE in the host OS while running the Python scripts in
the container's environment.

```
docker compose exec -it broker /bin/bash
root@c33f99226f72:/pulsar#
```

You may want to launch a second window with its own container shell for running the 
project Python scripts, then `cd /home`.


## Exploring behavior with `metar_ts.json`

The examples below assume that you have followed the Getting Started section and have:

1. Pulsar standalone running

2. An interactive shell in the broker container

3. A Python 3 venv with `pulsar-client` installed in your host OS, or an interactive shell
   in the broker container


### Reading from a persistent topic

1. Create a namespace with a default retention of 31 days and 500 MB.

   From the default container shell (with `/pulsar` as the working directory)

   ```shell
   bin/pulsar-admin namespaces create public/weather
   bin/pulsar-admin namespaces set-retention --time 31d --size 500M public/weather
   ```
   
2. Publish the first 10 messages from the METAR time series.

   From the host OS or a container shell with `/home` as the working directory

   ```
   python produce_json.py --topic persistent://public/weather/metar --count 10 --key station_id metar_ts.json      
   Published 10 messages to persistent://public/weather/metar
   ```

3. Read the messages in the `metar` topic.

   ```
   python read_json.py --topic persistent://public/weather/metar --print-each raw_text
   {'raw_text': 'KACK 100009Z 25010KT 8SM BKN007 BKN065 OVC100 27/25 A2994 RMK AO2 LTG DSNT W AND NW T02670250'}
   {'raw_text': 'KACK 100034Z 26009KT 8SM SCT006 BKN013 OVC055 26/25 A2996 RMK AO2 LTG DSNT W AND NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KCQX 100038Z AUTO 24004KT 8SM -RA FEW009 FEW110 26/24 A2993 RMK AO2 LTG DSNT SW RAB2358 P0000 T02610244'}
   {'raw_text': 'KACK 100046Z 25010KT 7SM SCT011 SCT021 BKN065 26/25 A2995 RMK AO2 LTG DSNT NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KMWN 100047Z 22010KT 0SM FG VV000 11/11 RMK'}
   {'raw_text': 'KCQX 100052Z AUTO VRB04KT 6SM -RA BR FEW009 FEW060 FEW110 26/24 A2994 RMK AO2 LTG DSNT SW RAB2358 SLP138 P0001 T02610244'}
   {'raw_text': 'KACK 100053Z 25010KT 7SM FEW013 SCT021 BKN120 26/25 A2994 RMK AO2 LTG DSNT NW RAB17E33 SLP140 P0001 T02610250'}
   {'raw_text': 'KBOS 100054Z 01008KT 6SM BR SCT007 SCT065 BKN130 OVC250 22/21 A2996 RMK AO2 PRESRR SLP146 T02220211 $'}
   {'raw_text': 'KBHB 100056Z AUTO 03007KT 10SM OVC017 18/16 A3002 RMK AO2 SLP167 T01780156 PNO $'}
   {'raw_text': 'KBOS 100103Z 01012KT 5SM BR BKN007 BKN085 OVC250 22/21 A2996 RMK AO2 T02170206 $'}
   Read 10 messages from persistent://public/weather/metar
   ```
   
   The first 10 messages correspond to the first 10 elements of the array in
   `metar_ts.json`. The observation date/time field, reported at day of month followed
   by time as HHmm in UTC is helpful for discerning successive reports for a station.
   For example, the ceiling and visibility at KACK, KCQX, and KBOS was changing enough
   over the course of the hour to warrant updates.

   A compacted read of the topic returns the same 10 messages.

   ```
   python read_json.py --topic persistent://public/weather/metar --print-each raw_text --compacted
   {'raw_text': 'KACK 100009Z 25010KT 8SM BKN007 BKN065 OVC100 27/25 A2994 RMK AO2 LTG DSNT W AND NW T02670250'}
   {'raw_text': 'KACK 100034Z 26009KT 8SM SCT006 BKN013 OVC055 26/25 A2996 RMK AO2 LTG DSNT W AND NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KCQX 100038Z AUTO 24004KT 8SM -RA FEW009 FEW110 26/24 A2993 RMK AO2 LTG DSNT SW RAB2358 P0000 T02610244'}
   {'raw_text': 'KACK 100046Z 25010KT 7SM SCT011 SCT021 BKN065 26/25 A2995 RMK AO2 LTG DSNT NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KMWN 100047Z 22010KT 0SM FG VV000 11/11 RMK'}
   {'raw_text': 'KCQX 100052Z AUTO VRB04KT 6SM -RA BR FEW009 FEW060 FEW110 26/24 A2994 RMK AO2 LTG DSNT SW RAB2358 SLP138 P0001 T02610244'}
   {'raw_text': 'KACK 100053Z 25010KT 7SM FEW013 SCT021 BKN120 26/25 A2994 RMK AO2 LTG DSNT NW RAB17E33 SLP140 P0001 T02610250'}
   {'raw_text': 'KBOS 100054Z 01008KT 6SM BR SCT007 SCT065 BKN130 OVC250 22/21 A2996 RMK AO2 PRESRR SLP146 T02220211 $'}
   {'raw_text': 'KBHB 100056Z AUTO 03007KT 10SM OVC017 18/16 A3002 RMK AO2 SLP167 T01780156 PNO $'}
   {'raw_text': 'KBOS 100103Z 01012KT 5SM BR BKN007 BKN085 OVC250 22/21 A2996 RMK AO2 T02170206 $'}
   Read 10 messages from persistent://public/weather/metar
   ```
   
4. Trigger compaction

   ```
   bin/pulsar-admin topics compact public/weather/metar
   Topic compaction requested for persistent://public/weather/metar
   ```

5. Compare a non-compacted and compacted read following topic compaction

   Non-compacted read:

   ```
   python read_json.py --topic persistent://public/weather/metar --print-each raw_text --timeout-millis 100
   {'raw_text': 'KACK 100009Z 25010KT 8SM BKN007 BKN065 OVC100 27/25 A2994 RMK AO2 LTG DSNT W AND NW T02670250'}
   {'raw_text': 'KACK 100034Z 26009KT 8SM SCT006 BKN013 OVC055 26/25 A2996 RMK AO2 LTG DSNT W AND NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KCQX 100038Z AUTO 24004KT 8SM -RA FEW009 FEW110 26/24 A2993 RMK AO2 LTG DSNT SW RAB2358 P0000 T02610244'}
   {'raw_text': 'KACK 100046Z 25010KT 7SM SCT011 SCT021 BKN065 26/25 A2995 RMK AO2 LTG DSNT NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KMWN 100047Z 22010KT 0SM FG VV000 11/11 RMK'}
   {'raw_text': 'KCQX 100052Z AUTO VRB04KT 6SM -RA BR FEW009 FEW060 FEW110 26/24 A2994 RMK AO2 LTG DSNT SW RAB2358 SLP138 P0001 T02610244'}
   {'raw_text': 'KACK 100053Z 25010KT 7SM FEW013 SCT021 BKN120 26/25 A2994 RMK AO2 LTG DSNT NW RAB17E33 SLP140 P0001 T02610250'}
   {'raw_text': 'KBOS 100054Z 01008KT 6SM BR SCT007 SCT065 BKN130 OVC250 22/21 A2996 RMK AO2 PRESRR SLP146 T02220211 $'}
   {'raw_text': 'KBHB 100056Z AUTO 03007KT 10SM OVC017 18/16 A3002 RMK AO2 SLP167 T01780156 PNO $'}
   {'raw_text': 'KBOS 100103Z 01012KT 5SM BR BKN007 BKN085 OVC250 22/21 A2996 RMK AO2 T02170206 $'}
   Read 10 messages from persistent://public/weather/metar
   ```

   Same 10 METAR observations as before with the same station IDs and timestamps.

   Compacted read:

   ```
   python read_json.py --topic persistent://public/weather/metar --print-each raw_text --compacted --timeout-millis 100 
   {'raw_text': 'KMWN 100047Z 22010KT 0SM FG VV000 11/11 RMK'}
   {'raw_text': 'KCQX 100052Z AUTO VRB04KT 6SM -RA BR FEW009 FEW060 FEW110 26/24 A2994 RMK AO2 LTG DSNT SW RAB2358 SLP138 P0001 T02610244'}
   {'raw_text': 'KACK 100053Z 25010KT 7SM FEW013 SCT021 BKN120 26/25 A2994 RMK AO2 LTG DSNT NW RAB17E33 SLP140 P0001 T02610250'}
   {'raw_text': 'KBHB 100056Z AUTO 03007KT 10SM OVC017 18/16 A3002 RMK AO2 SLP167 T01780156 PNO $'}
   {'raw_text': 'KBOS 100103Z 01012KT 5SM BR BKN007 BKN085 OVC250 22/21 A2996 RMK AO2 T02170206 $'}
   Read 5 messages from persistent://public/weather/metar
   ``` 
   
   This returns the most recent messages, based on publishing order, for each of the 5 
   unique `station_id` keys.

6. Examine the topic stats

   ```
   bin/pulsar-admin topics stats public/weather/metar
   {
     "msgRateIn" : 0.0,
     "msgThroughputIn" : 0.0,
     "msgRateOut" : 0.0,
     "msgThroughputOut" : 0.0,
     "bytesInCounter" : 10139,
     "msgInCounter" : 10,
     "bytesOutCounter" : 65864,
     "msgOutCounter" : 65,
     "averageMsgSize" : 0.0,
     "msgChunkPublished" : false,
     "storageSize" : 10139,
     "backlogSize" : 0,
     "offloadedStorageSize" : 0,
     "lastOffloadLedgerId" : 0,
     "lastOffloadSuccessTimeStamp" : 0,
     "lastOffloadFailureTimeStamp" : 0,
     "publishers" : [ ],
     "waitingPublishers" : 0,
     "subscriptions" : {
       "__compaction" : {
         "msgRateOut" : 0.0,
         "msgThroughputOut" : 0.0,
         "bytesOutCounter" : 20278,
         "msgOutCounter" : 20,
         "msgRateRedeliver" : 0.0,
         "chunkedMessageRate" : 0,
         "msgBacklog" : 0,
         "backlogSize" : 0,
         "msgBacklogNoDelayed" : 0,
         "blockedSubscriptionOnUnackedMsgs" : false,
         "msgDelayed" : 0,
         "unackedMessages" : 0,
         "type" : "Exclusive",
         "msgRateExpired" : 0.0,
         "totalMsgExpired" : 0,
         "lastExpireTimestamp" : 0,
         "lastConsumedFlowTimestamp" : 1660514477336,
         "lastConsumedTimestamp" : 0,
         "lastAckedTimestamp" : 0,
         "lastMarkDeleteAdvancedTimestamp" : 0,
         "consumers" : [ ],
         "isDurable" : true,
         "isReplicated" : false,
         "allowOutOfOrderDelivery" : false,
         "consumersAfterMarkDeletePosition" : { },
         "nonContiguousDeletedMessagesRanges" : 0,
         "nonContiguousDeletedMessagesRangesSerializedSize" : 0,
         "durable" : true,
         "replicated" : false
       }
     },
     "replication" : { },
     "deduplicationStatus" : "Disabled",
     "nonContiguousDeletedMessagesRanges" : 0,
     "nonContiguousDeletedMessagesRangesSerializedSize" : 0,
     "compaction" : {
       "lastCompactionRemovedEventCount" : 5,
       "lastCompactionSucceedTimestamp" : 1660514477358,
       "lastCompactionFailedTimestamp" : 0,
       "lastCompactionDurationTimeInMills" : 240
     }
   }
   ```
   
   Note:
   * a subscription for `__compaction`
   * the `compaction` attribute reports 5 events removed, which correlates to the message
     counts we observed comparing the non-compacted and compacted read

7. Publish the rest of the METAR time series

   ```
   python produce_json.py --topic persistent://public/weather/metar --first 10 --key station_id metar_ts.json
   Published 491 messages to persistent://public/weather/metar
   ```

8. A non-compacted read returns the complete set of messages published on the topic.

   ```
   python read_json.py --topic persistent://public/weather/metar --print-each raw_text --timeout-millis 100
   {'raw_text': 'KACK 100009Z 25010KT 8SM BKN007 BKN065 OVC100 27/25 A2994 RMK AO2 LTG DSNT W AND NW T02670250'}
   {'raw_text': 'KACK 100034Z 26009KT 8SM SCT006 BKN013 OVC055 26/25 A2996 RMK AO2 LTG DSNT W AND NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KCQX 100038Z AUTO 24004KT 8SM -RA FEW009 FEW110 26/24 A2993 RMK AO2 LTG DSNT SW RAB2358 P0000 T02610244'}
   {'raw_text': 'KACK 100046Z 25010KT 7SM SCT011 SCT021 BKN065 26/25 A2995 RMK AO2 LTG DSNT NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KMWN 100047Z 22010KT 0SM FG VV000 11/11 RMK'}
   <snip>
   {'raw_text': 'KBHB 122256Z AUTO 33003KT 10SM CLR 24/13 A2997 RMK AO2 SLP149 T02390128 $'}
   {'raw_text': 'KMWN 122347Z 32020KT 1/16SM -DZ FG VV001 04/04 RMK DZB35 60001 10072 20036'}
   {'raw_text': 'KCQX 122352Z AUTO 00000KT 10SM FEW100 21/18 A2999 RMK AO2 SLP158 T02060178 10239 20206 53008'}
   {'raw_text': 'KACK 122353Z 03003KT 10SM FEW100 21/19 A2999 RMK AO2 SLP155 T02060194 10239 20206 53009'}
   {'raw_text': 'KBOS 122354Z 07004KT 10SM FEW065 FEW080 SCT150 SCT220 20/15 A3002 RMK AO2 SLP165 TCU DSNT S T02000150 10250 20200 53018'}
   {'raw_text': 'KBHB 122356Z AUTO 00000KT 10SM CLR 21/13 A2999 RMK AO2 SLP157 T02060133 10261 20206 53015 $'}
   Read 501 messages from persistent://public/weather/metar
   ```

   Total size of the METAR time series is 501 records.

9. Try a compacted read before we trigger compaction again

   ```
   python read_json.py --topic persistent://public/weather/metar --print-each raw_text --compacted --timeout-millis 100
   {'raw_text': 'KMWN 100047Z 22010KT 0SM FG VV000 11/11 RMK'}
   {'raw_text': 'KCQX 100052Z AUTO VRB04KT 6SM -RA BR FEW009 FEW060 FEW110 26/24 A2994 RMK AO2 LTG DSNT SW RAB2358 SLP138 P0001 T02610244'}
   {'raw_text': 'KACK 100053Z 25010KT 7SM FEW013 SCT021 BKN120 26/25 A2994 RMK AO2 LTG DSNT NW RAB17E33 SLP140 P0001 T02610250'}
   {'raw_text': 'KBHB 100056Z AUTO 03007KT 10SM OVC017 18/16 A3002 RMK AO2 SLP167 T01780156 PNO $'}
   {'raw_text': 'KBOS 100103Z 01012KT 5SM BR BKN007 BKN085 OVC250 22/21 A2996 RMK AO2 T02170206 $'}
   <snip>
   {'raw_text': 'KBHB 122256Z AUTO 33003KT 10SM CLR 24/13 A2997 RMK AO2 SLP149 T02390128 $'}
   {'raw_text': 'KMWN 122347Z 32020KT 1/16SM -DZ FG VV001 04/04 RMK DZB35 60001 10072 20036'}
   {'raw_text': 'KCQX 122352Z AUTO 00000KT 10SM FEW100 21/18 A2999 RMK AO2 SLP158 T02060178 10239 20206 53008'}
   {'raw_text': 'KACK 122353Z 03003KT 10SM FEW100 21/19 A2999 RMK AO2 SLP155 T02060194 10239 20206 53009'}
   {'raw_text': 'KBOS 122354Z 07004KT 10SM FEW065 FEW080 SCT150 SCT220 20/15 A3002 RMK AO2 SLP165 TCU DSNT S T02000150 10250 20200 53018'}
   {'raw_text': 'KBHB 122356Z AUTO 00000KT 10SM CLR 21/13 A2999 RMK AO2 SLP157 T02060133 10261 20206 53015 $'}
   Read 496 messages from persistent://public/weather/metar
   ```

   We get the same first 5 messages as the previous compacted read, followed by the 491 
   new messages.

10. Trigger compaction a second time and check stats

   ```
   bin/pulsar-admin topics compact  public/weather/metar
   Topic compaction requested for persistent://public/weather/metar
   root@c33f99226f72:/pulsar# bin/pulsar-admin topics stats  public/weather/metar
   <snip>
     "compaction" : {
       "lastCompactionRemovedEventCount" : 491,
       "lastCompactionSucceedTimestamp" : 1660515901985,
       "lastCompactionFailedTimestamp" : 0,
       "lastCompactionDurationTimeInMills" : 378
     }
   }
   ```

11. A compacted read now returns the 5 most recent messages for each `station_id`

   ```
   python read_json.py --topic persistent://public/weather/metar --print-each raw_text --compacted --timeout-millis 100
   {'raw_text': 'KMWN 122347Z 32020KT 1/16SM -DZ FG VV001 04/04 RMK DZB35 60001 10072 20036'}
   {'raw_text': 'KCQX 122352Z AUTO 00000KT 10SM FEW100 21/18 A2999 RMK AO2 SLP158 T02060178 10239 20206 53008'}
   {'raw_text': 'KACK 122353Z 03003KT 10SM FEW100 21/19 A2999 RMK AO2 SLP155 T02060194 10239 20206 53009'}
   {'raw_text': 'KBOS 122354Z 07004KT 10SM FEW065 FEW080 SCT150 SCT220 20/15 A3002 RMK AO2 SLP165 TCU DSNT S T02000150 10250 20200 53018'}
   {'raw_text': 'KBHB 122356Z AUTO 00000KT 10SM CLR 21/13 A2999 RMK AO2 SLP157 T02060133 10261 20206 53015 $'}
   Read 5 messages from persistent://public/weather/metar
   ```

   A non-compacted read will still return all 501 messages (until the retention
   expires).


### Compaction has no effect on messages published without a partition key

This experiment assumes you have created the `public/weather` namespace. If not, see the 
_Create a namespace with a default retention..._ instruction above.

1. Publish the first 10 messages from the METAR time series, but without a designated key

   ```
   python produce_json.py --topic persistent://public/weather/metar-nokey --count 10 metar_ts.json      
   Published 10 messages to persistent://public/weather/metar-nokey
   ```

2. Trigger compaction and check stats

   ```
   bin/pulsar-admin topics compact public/weather/metar-nokey
   Topic compaction requested for persistent://public/weather/metar-nokey
   ```

   10 messages in, but none removed by compaction:

   ```
   bin/pulsar-admin topics stats public/weather/metar-nokey
   {
     "msgRateIn" : 0.0,
     "msgThroughputIn" : 0.0,
     "msgRateOut" : 0.0,
     "msgThroughputOut" : 0.0,
     "bytesInCounter" : 10079,
     "msgInCounter" : 10,
    <snip>
     "compaction" : {
       "lastCompactionRemovedEventCount" : 0,
       "lastCompactionSucceedTimestamp" : 1660517301713,
       "lastCompactionFailedTimestamp" : 0,
       "lastCompactionDurationTimeInMills" : 224
     }
   }
   ```

3. Compacted read returns all 10 messages

   ```
   python read_json.py --topic persistent://public/weather/metar-nokey --print-each raw_text --compacted --timeout-millis 100
   {'raw_text': 'KACK 100009Z 25010KT 8SM BKN007 BKN065 OVC100 27/25 A2994 RMK AO2 LTG DSNT W AND NW T02670250'}
   {'raw_text': 'KACK 100034Z 26009KT 8SM SCT006 BKN013 OVC055 26/25 A2996 RMK AO2 LTG DSNT W AND NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KCQX 100038Z AUTO 24004KT 8SM -RA FEW009 FEW110 26/24 A2993 RMK AO2 LTG DSNT SW RAB2358 P0000 T02610244'}
   {'raw_text': 'KACK 100046Z 25010KT 7SM SCT011 SCT021 BKN065 26/25 A2995 RMK AO2 LTG DSNT NW RAB17E33 P0001 T02610250'}
   {'raw_text': 'KMWN 100047Z 22010KT 0SM FG VV000 11/11 RMK'}
   {'raw_text': 'KCQX 100052Z AUTO VRB04KT 6SM -RA BR FEW009 FEW060 FEW110 26/24 A2994 RMK AO2 LTG DSNT SW RAB2358 SLP138 P0001 T02610244'}
   {'raw_text': 'KACK 100053Z 25010KT 7SM FEW013 SCT021 BKN120 26/25 A2994 RMK AO2 LTG DSNT NW RAB17E33 SLP140 P0001 T02610250'}
   {'raw_text': 'KBOS 100054Z 01008KT 6SM BR SCT007 SCT065 BKN130 OVC250 22/21 A2996 RMK AO2 PRESRR SLP146 T02220211 $'}
   {'raw_text': 'KBHB 100056Z AUTO 03007KT 10SM OVC017 18/16 A3002 RMK AO2 SLP167 T01780156 PNO $'}
   {'raw_text': 'KBOS 100103Z 01012KT 5SM BR BKN007 BKN085 OVC250 22/21 A2996 RMK AO2 T02170206 $'}
   Read 10 messages from persistent://public/weather/metar-nokey
   ```

At this point, the messages without a key will remain in the topic until their retention
expires and will not be reduced by compaction.


### Reader with `MessageId.latest` and `.earliest` positions

If the most recent message on a topic is desired, regardless of key, does a reader with
the starting position as `MessageId.latest` yield that message?

A careful reading of the docs suggests, no, but here is a simple experiment to
demonstrate the behavior.

This experiment assumes you have created the `public/weather` namespace. If not, see the
_Create a namespace with a default retention..._ instruction above.

1. Publish the first 10 messages from the METAR time series.

   ```
   python produce_json.py --topic persistent://public/weather/metar --count 10 --key station_id metar_ts.json      
   Published 10 messages to persistent://public/weather/metar
   ```
   
2. Start interactive python session

   ```pycon
   python
   Python 3.8.10 (default, Nov 26 2021, 20:14:08) 
   [GCC 9.3.0] on linux
   Type "help", "copyright", "credits" or "license" for more information.
   >>>
   ```

   
3. Connect to the broker

   ```pycon
   >>> import pulsar
   >>> import read_json
   >>> client = pulsar.Client('pulsar://localhost:6650')
   ```

4. First, try a reader with `MessageId.latest` as initial position

    ```pycon
    >>> reader = client.create_reader('persistent://public/weather/metar',pulsar.MessageId.latest)
    2022-08-14 23:07:23.815 INFO  [139820526454592] ClientConnection:182 | [<none> -> pulsar://localhost:6650] Create ClientConnection, timeout=10000
    2022-08-14 23:07:23.815 INFO  [139820526454592] ConnectionPool:96 | Created connection for pulsar://localhost:6650
    2022-08-14 23:07:23.816 INFO  [139820494239488] ClientConnection:368 | [127.0.0.1:39636 -> 127.0.0.1:6650] Connected to broker
    2022-08-14 23:07:23.820 INFO  [139820494239488] HandlerBase:64 | [persistent://public/weather/metar, reader-7994ad2659, 0] Getting connection from pool
    2022-08-14 23:07:23.822 INFO  [139820494239488] ConsumerImpl:216 | [persistent://public/weather/metar, reader-7994ad2659, 0] Created consumer on broker [127.0.0.1:39636 -> 127.0.0.1:6650]
    >>> reader.has_message_available()
    False
    ```
   
    Even though we published messages to the topic, no messages are available to reader
    at this position.

5. Try to read anyway

   ```pycon
   >>> metars = list(read_json.read_available(reader, timeout_millis=1000))
   >>> len(metars)
   0
   ```

   Nada.

6. Seek to `MessageId.earliest`.

   ```pycon
   >>> reader.seek(pulsar.MessageId.earliest)
   2022-08-14 23:14:32.496 INFO  [139820494239488] ConsumerImpl:855 | Broker notification of Closed consumer: 0
   2022-08-14 23:14:32.496 INFO  [139820494239488] HandlerBase:142 | [persistent://public/weather/metar, reader-7994ad2659, 0] Schedule reconnection in 0.1 s
   2022-08-14 23:14:32.497 INFO  [139820494239488] ConsumerImpl:1082 | [persistent://public/weather/metar, reader-7994ad2659, 0] Seek successfully
   >>> 2022-08-14 23:14:32.597 INFO  [139820494239488] HandlerBase:64 | [persistent://public/weather/metar, reader-7994ad2659, 0] Getting connection from pool
   2022-08-14 23:14:32.599 INFO  [139820494239488] ConsumerImpl:216 | [persistent://public/weather/metar, reader-7994ad2659, 0] Created consumer on broker [127.0.0.1:39636 -> 127.0.0.1:6650]
   >>> reader.has_message_available()
   True
   ```
   
   This looks more promising.

   ```pycon
   >>> metars = list(read_json.read_available(reader, timeout_millis=1000))
   >>> len(metars)
   10
   ```

   Indeed, we were able to read the 10 messages we published, like we've seen before.

   ```pycon
   >>> print('\n'.join(m['raw_text'] for m in metars))
   KACK 100009Z 25010KT 8SM BKN007 BKN065 OVC100 27/25 A2994 RMK AO2 LTG DSNT W AND NW T02670250
   KACK 100034Z 26009KT 8SM SCT006 BKN013 OVC055 26/25 A2996 RMK AO2 LTG DSNT W AND NW RAB17E33 P0001 T02610250
   KCQX 100038Z AUTO 24004KT 8SM -RA FEW009 FEW110 26/24 A2993 RMK AO2 LTG DSNT SW RAB2358 P0000 T02610244
   KACK 100046Z 25010KT 7SM SCT011 SCT021 BKN065 26/25 A2995 RMK AO2 LTG DSNT NW RAB17E33 P0001 T02610250
   KMWN 100047Z 22010KT 0SM FG VV000 11/11 RMK
   KCQX 100052Z AUTO VRB04KT 6SM -RA BR FEW009 FEW060 FEW110 26/24 A2994 RMK AO2 LTG DSNT SW RAB2358 SLP138 P0001 T02610244
   KACK 100053Z 25010KT 7SM FEW013 SCT021 BKN120 26/25 A2994 RMK AO2 LTG DSNT NW RAB17E33 SLP140 P0001 T02610250
   KBOS 100054Z 01008KT 6SM BR SCT007 SCT065 BKN130 OVC250 22/21 A2996 RMK AO2 PRESRR SLP146 T02220211 $
   KBHB 100056Z AUTO 03007KT 10SM OVC017 18/16 A3002 RMK AO2 SLP167 T01780156 PNO $
   KBOS 100103Z 01012KT 5SM BR BKN007 BKN085 OVC250 22/21 A2996 RMK AO2 T02170206 $
   >>>
   ```



