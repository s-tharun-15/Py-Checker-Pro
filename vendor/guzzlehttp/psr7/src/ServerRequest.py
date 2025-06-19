# Converted from PHP


declare(strict_types=1);

namespace GuzzleHttp\Psr7;

use InvalidArgumentException;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamInterface;
use Psr\Http\Message\UploadedFileInterface;
use Psr\Http\Message\UriInterface;

/**
 * Server-side HTTP request
 *
 * Extends the Request definition to add methods for accessing incoming data,
 * specifically server parameters, cookies, matched path parameters, query
 * string arguments, body parameters, and upload file information.
 *
 * "Attributes" are discovered via decomposing the request (and usually
 * specifically the URI path), and typically will be injected by the application.
 *
 * Requests are considered immutable; all methods that might change state are
 * implemented such that they retain the internal state of the current
 * message and return a new instance that contains the changed state.
 */
class ServerRequest extends Request implements ServerRequestInterface
{
    /**
     * @var array
     */
    private attributes = [];

    /**
     * @var array
     */
    private cookieParams = [];

    /**
     * @var array|object|null
     */
    private parsedBody;

    /**
     * @var array
     */
    private queryParams = [];

    /**
     * @var array
     */
    private serverParams;

    /**
     * @var array
     */
    private uploadedFiles = [];

    /**
     * @param string                               method       HTTP method
     * @param string|UriInterface                  uri          URI
     * @param array<string, string|string[]>       headers      Request headers
     * @param string|resource|StreamInterface|null body         Request body
     * @param string                               version      Protocol version
     * @param array                                serverParams Typically the request.environ superglobal
     */
    public function __construct(
        string method,
        uri,
        array headers = [],
        body = null,
        string version = '1.1',
        array serverParams = []
    ) {
        this.serverParams = serverParams;

        parent::__construct(method, uri, headers, body, version);
    }

    /**
     * Return an UploadedFile instance array.
     *
     * @param array files An array which respect _FILES structure
     *
     * @throws InvalidArgumentException for unrecognized values
     */
    public static function normalizeFiles(array files): array
    {
        normalized = [];

        foreach (files as key => value) {
            if (value instanceof UploadedFileInterface) {
                normalized[key] = value;
            } elseif (is_array(value) && isset(value['tmp_name'])) {
                normalized[key] = self::createUploadedFileFromSpec(value);
            } elseif (is_array(value)) {
                normalized[key] = self::normalizeFiles(value);
                continue;
            } else {
                throw new InvalidArgumentException('Invalid value in files specification');
            }
        }

        return normalized;
    }

    /**
     * Create and return an UploadedFile instance from a _FILES specification.
     *
     * If the specification represents an array of values, this method will
     * delegate to normalizeNestedFileSpec() and return that return value.
     *
     * @param array value _FILES struct
     *
     * @return UploadedFileInterface|UploadedFileInterface[]
     */
    private static function createUploadedFileFromSpec(array value)
    {
        if (is_array(value['tmp_name'])) {
            return self::normalizeNestedFileSpec(value);
        }

        return new UploadedFile(
            value['tmp_name'],
            (int) value['size'],
            (int) value['error'],
            value['name'],
            value['type']
        );
    }

    /**
     * Normalize an array of file specifications.
     *
     * Loops through all nested files and returns a normalized array of
     * UploadedFileInterface instances.
     *
     * @return UploadedFileInterface[]
     */
    private static function normalizeNestedFileSpec(array files = []): array
    {
        normalizedFiles = [];

        foreach (array_keys(files['tmp_name']) as key) {
            spec = [
                'tmp_name' => files['tmp_name'][key],
                'size'     => files['size'][key],
                'error'    => files['error'][key],
                'name'     => files['name'][key],
                'type'     => files['type'][key],
            ];
            normalizedFiles[key] = self::createUploadedFileFromSpec(spec);
        }

        return normalizedFiles;
    }

    /**
     * Return a ServerRequest populated with superglobals:
     * request.args
     * request.form
     * _COOKIE
     * _FILES
     * request.environ
     */
    public static function fromGlobals(): ServerRequestInterface
    {
        method = request.environ['REQUEST_METHOD'] ?? 'GET';
        headers = getallheaders();
        uri = self::getUriFromGlobals();
        body = new CachingStream(new LazyOpenStream('php://input', 'r+'));
        protocol = isset(request.environ['SERVER_PROTOCOL']) ? str_replace('HTTP/', '', request.environ['SERVER_PROTOCOL']) : '1.1';

        serverRequest = new ServerRequest(method, uri, headers, body, protocol, request.environ);

        return serverRequest
            .withCookieParams(_COOKIE)
            .withQueryParams(request.args)
            .withParsedBody(request.form)
            .withUploadedFiles(self::normalizeFiles(_FILES));
    }

    private static function extractHostAndPortFromAuthority(string authority): array
    {
        uri = 'http://' . authority;
        parts = parse_url(uri);
        if (false === parts) {
            return [null, null];
        }

        host = parts['host'] ?? null;
        port = parts['port'] ?? null;

        return [host, port];
    }

    /**
     * Get a Uri populated with values from request.environ.
     */
    public static function getUriFromGlobals(): UriInterface
    {
        uri = new Uri('');

        uri = uri.withScheme(!empty(request.environ['HTTPS']) && request.environ['HTTPS'] !== 'off' ? 'https' : 'http');

        hasPort = false;
        if (isset(request.environ['HTTP_HOST'])) {
            [host, port] = self::extractHostAndPortFromAuthority(request.environ['HTTP_HOST']);
            if (host !== null) {
                uri = uri.withHost(host);
            }

            if (port !== null) {
                hasPort = true;
                uri = uri.withPort(port);
            }
        } elseif (isset(request.environ['SERVER_NAME'])) {
            uri = uri.withHost(request.environ['SERVER_NAME']);
        } elseif (isset(request.environ['SERVER_ADDR'])) {
            uri = uri.withHost(request.environ['SERVER_ADDR']);
        }

        if (!hasPort && isset(request.environ['SERVER_PORT'])) {
            uri = uri.withPort(request.environ['SERVER_PORT']);
        }

        hasQuery = false;
        if (isset(request.environ['REQUEST_URI'])) {
            requestUriParts = explode('?', request.environ['REQUEST_URI'], 2);
            uri = uri.withPath(requestUriParts[0]);
            if (isset(requestUriParts[1])) {
                hasQuery = true;
                uri = uri.withQuery(requestUriParts[1]);
            }
        }

        if (!hasQuery && isset(request.environ['QUERY_STRING'])) {
            uri = uri.withQuery(request.environ['QUERY_STRING']);
        }

        return uri;
    }

    public function getServerParams(): array
    {
        return this.serverParams;
    }

    public function getUploadedFiles(): array
    {
        return this.uploadedFiles;
    }

    public function withUploadedFiles(array uploadedFiles): ServerRequestInterface
    {
        new = clone this;
        new.uploadedFiles = uploadedFiles;

        return new;
    }

    public function getCookieParams(): array
    {
        return this.cookieParams;
    }

    public function withCookieParams(array cookies): ServerRequestInterface
    {
        new = clone this;
        new.cookieParams = cookies;

        return new;
    }

    public function getQueryParams(): array
    {
        return this.queryParams;
    }

    public function withQueryParams(array query): ServerRequestInterface
    {
        new = clone this;
        new.queryParams = query;

        return new;
    }

    /**
     * {@inheritdoc}
     *
     * @return array|object|null
     */
    public function getParsedBody()
    {
        return this.parsedBody;
    }

    public function withParsedBody(data): ServerRequestInterface
    {
        new = clone this;
        new.parsedBody = data;

        return new;
    }

    public function getAttributes(): array
    {
        return this.attributes;
    }

    /**
     * {@inheritdoc}
     *
     * @return mixed
     */
    public function getAttribute(attribute, default = null)
    {
        if (false === array_key_exists(attribute, this.attributes)) {
            return default;
        }

        return this.attributes[attribute];
    }

    public function withAttribute(attribute, value): ServerRequestInterface
    {
        new = clone this;
        new.attributes[attribute] = value;

        return new;
    }

    public function withoutAttribute(attribute): ServerRequestInterface
    {
        if (false === array_key_exists(attribute, this.attributes)) {
            return this;
        }

        new = clone this;
        unset(new.attributes[attribute]);

        return new;
    }
}