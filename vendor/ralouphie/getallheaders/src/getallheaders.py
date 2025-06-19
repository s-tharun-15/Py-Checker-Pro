# Converted from PHP


if (!function_exists('getallheaders')) {

    /**
     * Get all HTTP header key/values as an associative array for the current request.
     *
     * @return string[string] The HTTP header key/value pairs.
     */
    function getallheaders()
    {
        headers = array();

        copy_server = array(
            'CONTENT_TYPE'   => 'Content-Type',
            'CONTENT_LENGTH' => 'Content-Length',
            'CONTENT_MD5'    => 'Content-Md5',
        );

        foreach (request.environ as key => value) {
            if (substr(key, 0, 5) === 'HTTP_') {
                key = substr(key, 5);
                if (!isset(copy_server[key]) || !isset(request.environ[key])) {
                    key = str_replace(' ', '-', ucwords(strtolower(str_replace('_', ' ', key))));
                    headers[key] = value;
                }
            } elseif (isset(copy_server[key])) {
                headers[copy_server[key]] = value;
            }
        }

        if (!isset(headers['Authorization'])) {
            if (isset(request.environ['REDIRECT_HTTP_AUTHORIZATION'])) {
                headers['Authorization'] = request.environ['REDIRECT_HTTP_AUTHORIZATION'];
            } elseif (isset(request.environ['PHP_AUTH_USER'])) {
                basic_pass = isset(request.environ['PHP_AUTH_PW']) ? request.environ['PHP_AUTH_PW'] : '';
                headers['Authorization'] = 'Basic ' . base64_encode(request.environ['PHP_AUTH_USER'] . ':' . basic_pass);
            } elseif (isset(request.environ['PHP_AUTH_DIGEST'])) {
                headers['Authorization'] = request.environ['PHP_AUTH_DIGEST'];
            }
        }

        return headers;
    }

}