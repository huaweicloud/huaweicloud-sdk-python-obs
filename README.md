Version 3.19.7.1

New Features:
1. Supports obtaining access keys in customized mode to create an instance of ObsClient. Currently, users can obtain access keys from environment variables or obtain temporary access keys from the ECS server. Or users can customize other obtaining methods. Multiple methods can be combined to obtain access keys. In this case, users can obtain access keys by using the methods in sequence or by specifying which method goes first.

Documentation & Demo:
1. Added the security_providers and security_provider_policy parameters to section "Initializing an Instance of ObsClient" in OBS Python SDK API Reference.
2. Added the code example for obtaining access keys to create an instance of ObsClient in predefined mode to section "Initializing an Instance of ObsClient" in OBS Python SDK API Reference.
3. Added the code examples for obtaining access keys in predefined mode and in combination mode to section "Creating an Instance of ObsClient" in OBS Python SDK Developer Guide.
4. Added the security_providers and security_provider_policy parameters to section "Configuring an Instance of ObsClient" in OBS Python SDK Developer Guide.

Resolved Issues:
-------------------------------------------------------------------------------------------------

Version 3.19.5.1

Documentation & Demo
1. Added the description of the max_redirect_count parameter in the OBS client initialization section of the API Reference.
2. Added the description of the max_redirect_count parameter in the OBS client initialization section of the Developer Guide.

Resolved issues:
1. Fixed the issue that infinite number of redirects, resulting in an infinite loop.

-------------------------------------------------------------------------------------------------

Version 3.19.5
Updated the version ID format. The new version ID is named in the following format: Main version ID.Year ID.Month ID.

New features:
1. Additional header field is added to the resumable upload API uploadFile. You can set parameters such as acl, storageClass in the header.
2. By default, error-level logs are added to the non-2xx response statuses of OBS.

Documentation & Demo
1. Added the description of the additional header fields for resumable upload in the section about data types in the API Reference.
2. Added the section about predefined constant in the API Reference. The value of BUCKET_OWNER_FULL_CONTROL is added to the predefined access control policies.
3. Added the creation and usage of temporary access keys in the "Getting Started" section of the Developer Guide.

Resolved issues:
1. When the GET request is initiated and the server returns 302 redirection, the issue that new request does not extract the complete location information is fixed.
2. Fixed the issue that the process exits abnormally due to logrotate in special scenarios.
3. Optimized the resumable upload API uploadFile. The default part size is changed to 9 MB.
4. Fixed the issue that bucketClient does not support bucket encryption APIs.

-------------------------------------------------------------------------------------------------

Version 3.1.4
New features:

Documentation & Demo

Resolved issues:
1. Fixed the issue that uploading objects in chunk mode does not comply with HTTP regulations.
2. Fixed the issue that the progress is not cleared immediately in an error scenario if the progress bar is enabled for the following APIs: ObsClient.putContent, ObsClient.putObject, ObsClient.putFile, ObsClient.appendObject, and ObsClient.uploadPart.
3. Fixed the issue that ObsClient.initLog may cause log conflicts by modifying that the logging of ObsClient does not inherit the parent configuration.
4. Fixed the issue that ObsClient.close fails to close the log file handle correctly.

-------------------------------------------------------------------------------------------------

Version 3.1.2.1
New features:
1. Added bucket encryption APIs: ObsClient.setBucketEncryption, ObsClient.getBucketEncryption, and ObsClient.deleteBucketEncryption. Currently, only the SSE-KMS encryption is supported.
2. Added the identifier indicating whether to automatically close the input stream in the following APIs: ObsClient.putContent, ObsClient.putObject, ObsClient.appendObject, and ObsClient.uploadPart. The default value is true.

Documentation & Demo

Resolved issues:
1. Fixed the issue that multiple subprocesses are forked when ObsClient is initialized for multiple times in the Linux OS.


-------------------------------------------------------------------------------------------------
Version 3.1.2
New features:
1. FunctionGraph configuration and query are supported in the bucket event notification APIs: ObsClient.setBucketNotification and ObsClient.getBucketNotification.
2. Added the image processing parameters to the resumable download API ObsClient.downloadFile.
3. Added the batch download API ObsClient.downloadFiles to support download of objects by specified prefix, progress return, automatic multipart download of large files, and resumable download.

Documentation & Demo
1. Added the description of FunctionGraph configuration in the section about event notification in the Developer Guide.
2. Added the parameter description of FunctionGraph configuration in sections related to configuring and obtaining bucket notification in the API Reference.
3. Modified the sample code for enabling the bucket logging in the section related to access logs in the Developer Guide.

Resolved issues:
1. Fixed the issue that the error information reported by the bucket creation API ObsClient.createBucket is incorrect due to protocol negotiation.
2. Rectified the error of the SetBucketLogging function in the sample code examples/obs_python_sample.py.
3. Fixed the issue that the contentDisposition parameter is incorrectly processed by the object upload API ObsClient.setObjectMetadata in the SDK.
4. Modified the coding policy of special characters in the object temporary authentication access API ObsClient.createSignedUrl. Tilde (~) is used as the reserved character of the URL encoding to solve the problem that results are inconsistent in the Python2.x and 3.x environments.
5. Optimized the bottom-layer code to improve the SDK performance in uploading and downloading small files in the Python2.x environment.
6. Fixed the issue that the process is forked when the OBS package is imported to the Linux OS.
