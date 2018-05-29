============
Introduction
============

LAS is a public file format meant to exchange 3D point data, mostly used to exchange lidar point clouds.
LAZ is a **lossless** compression of the LAS format.

The latest LAS specification is the `LAS 1.4`_. pylas supports LAS files from Version 1.2 to 1.4.

.. _LAS 1.4: https://www.asprs.org/wp-content/uploads/2010/12/LAS_1_4_r13.pdf

LAS files are organized in 3 main parts:

1) Header
2) VLRs
3) Point Records


The header contains information about the data such as its version, the point format (which tells the different
dimensions stored for each points).

After the header, LAS files may contain VLRs (Variable Length Record).
VLRs are meant to store additional information such as the SRS, description on extra dimensions added to the points.
VLRs are divided in two parts:

1) header
2) payload

The payload is limited to 65,535 bytes (Because in the header, the length of the payload is stored on a uint16).

The last chunk of data (and the biggest one) contains the point records. In a LAS file, points are stored sequentially.

Version 1.4 of the LAS specification added a last block following the point records: EVLRs (Extended Variable
Length Record) which are the same thing as VLRs but they can carry a higher payload (length of the payload is stored
on a uint64)

Point Records
-------------

The point records holds the point cloud data the LAS Spec specifies 10 point formats.
A point format describe the dimensions stored for each point in the record.

Each LAS specification added new point formats, the table below describe the compatibility between point formats
and LAS file version.

+-----------------+-----------------------------------+
|LAS file version + Compatible point formats          |
+=================+===================================+
|1.2              | 0, 1, 2, 3                        |
+-----------------+-----------------------------------+
|1.3              | 0, 1, 2, 3, 4, 5                  |
+-----------------+-----------------------------------+
|1.4              | 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10  |
+-----------------+-----------------------------------+

* Point Format 0 *

+-------------------+
| Dimensions        |
+===================+
| X                 |
+-------------------+
| Y                 |
+-------------------+
| Z                 |
+-------------------+
| intensity         |
+-------------------+
| bit_fields        |
+-------------------+
| raw_classification|
+-------------------+
| scan_angle_rank   |
+-------------------+
| user_data         |
+-------------------+
| point_source_id   |
+-------------------+


The point formats 1, 2, 3, 4, 5 are based on the point format 0, meaning that they have
the same dimensions plus some additional dimensions:

* Point Format 1

+------------------+
| Added dimensions |
+==================+
| gps_time         |
+------------------+


* Point Format 2

+------------------+
| Added dimensions |
+==================+
| red              |
+------------------+
| green            |
+------------------+
| blue             |
+------------------+

* Point Format 3

+------------------+
| Added dimensions |
+==================+
| gps_time         |
+------------------+
| red              |
+------------------+
| green            |
+------------------+
| blue             |
+------------------+


* Point Format 4

+---------------------------+
| Added dimensions          |
+===========================+
| gps_time                  |
+---------------------------+
|wavepacket_index           |
+---------------------------+
|wavepacket_offset          |
+---------------------------+
|wavepacket_size            |
+---------------------------+
|return_point_wave_location |
+---------------------------+
|x_t                        |
+---------------------------+
|y_t                        |
+---------------------------+
|z_t                        |
+---------------------------+


* Point Format 5

+---------------------------+
| Added dimensions          |
+===========================+
| gps_time                  |
+---------------------------+
| red                       |
+---------------------------+
| green                     |
+---------------------------+
| blue                      |
+---------------------------+
|wavepacket_index           |
+---------------------------+
|wavepacket_offset          |
+---------------------------+
|wavepacket_size            |
+---------------------------+
|return_point_wave_location |
+---------------------------+
|x_t                        |
+---------------------------+
|y_t                        |
+---------------------------+
|z_t                        |
+---------------------------+

