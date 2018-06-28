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


VLRs
----

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

The names written in the tables below are the one you will have to use in
your code.

* Point Format 0 *

+----------------------+-----------+--------------+
| Dimensions           |   Type    |  Size (bit)  |
+======================+===========+==============+
| X                    |  signed   |      32      |
+----------------------+-----------+--------------+
| Y                    |  signed   |      32      |
+----------------------+-----------+--------------+
| Z                    |  signed   |      32      |
+----------------------+-----------+--------------+
| intensity            | unsigned  |      16      |
+----------------------+-----------+--------------+
| return_number        | unsigned  |      3       |
+----------------------+-----------+--------------+
| number_of_returns    | unsigned  |      3       |
+----------------------+-----------+--------------+
| scan_direction_flag  | bool      |      1       |
+----------------------+-----------+--------------+
| edge_of_flight_line  | bool      |      1       |
+----------------------+-----------+--------------+
| classification       | unsigned  |      5       |
+----------------------+-----------+--------------+
| synthetic            | bool      |      1       |
+----------------------+-----------+--------------+
| key_point            | signed    |      8       |
+----------------------+-----------+--------------+
| withheld             | signed    |      8       |
+----------------------+-----------+--------------+
| scan_angle_rank      | signed    |      8       |
+----------------------+-----------+--------------+
| user_data            | unsigned  |      8       |
+----------------------+-----------+--------------+
| point_source_id      | unsigned  |      8       |
+----------------------+-----------+--------------+


The point formats 1, 2, 3, 4, 5 are based on the point format 0, meaning that they have
the same dimensions plus some additional dimensions:

* Point Format 1

+----------------------+-----------+--------------+
| Added dimensions     |   Type    |  Size (bit)  |
+======================+===========+==============+
| gps_time             |  Floating |      64      |
+----------------------+-----------+--------------+


* Point Format 2

+----------------------+-----------+--------------+
| Added dimensions     |   Type    |  Size (bit)  |
+======================+===========+==============+
| red                  |  unsigned |      16      |
+----------------------+-----------+--------------+
| green                |  unsigned |      16      |
+----------------------+-----------+--------------+
| blue                 |  unsigned |      16      |
+----------------------+-----------+--------------+

* Point Format 3

+----------------------+-----------+--------------+
| Added dimensions     |   Type    |  Size (bit)  |
+======================+===========+==============+
| gps_time             |  Floating |      64      |
+----------------------+-----------+--------------+
| red                  |  unsigned |      16      |
+----------------------+-----------+--------------+
| green                |  unsigned |      16      |
+----------------------+-----------+--------------+
| blue                 |  unsigned |      16      |
+----------------------+-----------+--------------+


* Point Format 4

+----------------------------+-----------+--------------+
| Added dimensions           |   Type    |  Size (bit)  |
+============================+===========+==============+
| gps_time                   |  Floating |       64     |
+----------------------------+-----------+--------------+
| wavepacket_index           | unsigned  |      8       |
+----------------------------+-----------+--------------+
| wavepacket_offset          | unsigned  |      64      |
+----------------------------+-----------+--------------+
| wavepacket_size            | unsigned  |      32      |
+----------------------------+-----------+--------------+
| return_point_wave_location | unsigned  |      32      |
+----------------------------+-----------+--------------+
|x_t                         | floating  |      32      |
+----------------------------+-----------+--------------+
|y_t                         | floating  |      32      |
+----------------------------+-----------+--------------+
| z_t                        | floating  |      32      |
+----------------------------+-----------+--------------+

* Point Format 5

+----------------------------+-----------+--------------+
| Added dimensions           |   Type    |  Size (bit)  |
+============================+===========+==============+
| gps_time                   |  Floating |       64     |
+----------------------------+-----------+--------------+
| red                        |  unsigned |      16      |
+----------------------------+-----------+--------------+
| green                      |  unsigned |      16      |
+----------------------------+-----------+--------------+
| blue                       |  unsigned |      16      |
+----------------------------+-----------+--------------+
| wavepacket_index           | unsigned  |      8       |
+----------------------------+-----------+--------------+
| wavepacket_offset          | unsigned  |      64      |
+----------------------------+-----------+--------------+
| wavepacket_size            | unsigned  |      32      |
+----------------------------+-----------+--------------+
| return_point_wave_location | unsigned  |      32      |
+----------------------------+-----------+--------------+
|x_t                         | floating  |      32      |
+----------------------------+-----------+--------------+
|y_t                         | floating  |      32      |
+----------------------------+-----------+--------------+
| z_t                        | floating  |      32      |
+----------------------------+-----------+--------------+

